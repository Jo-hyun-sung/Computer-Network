"""평가 스크립트 (P5).

실험 폴더(들)의 labels / alerts / actions / features 를 읽어
docs/data-format.md 4장 정의대로 성능표를 자동 계산합니다.

    python3 eval/evaluate.py data/runs/<run_id> [...]        # 특정 실험
    python3 eval/evaluate.py --all                            # data/runs 전체
    python3 eval/evaluate.py --all --out eval/results/summary.md

여러 탐지기(규칙/AI/혼합)의 경보 파일을 모두 읽어 detector별로 나눠 집계합니다:
  alerts.jsonl, alerts_rule.jsonl, alerts_ai.jsonl (있는 것만)

지표(4장):
  - 맞은 경보(TP): attack이 같고 ts가 [start, end+GRACE]인 label이 있는 경보
  - 공격자 오지정: attack은 맞지만 attacker.mac이 label과 다름 → 틀린 경보(FP)
    (단, 경보의 attacker.mac이 null이면 '미지정'으로 보고 FP로 세지 않음)
  - 탐지율: 경보가 1개 이상 난 공격 수 / 전체 공격 수
  - 탐지 시간: 첫 TP 경보 ts − start_ts
  - 대응 시간: 그 공격의 첫 block action ts − start_ts
  - 오탐: 정상 구간(공격 밖) 경보 개수와, 정상 창 중 경보가 난 창 비율
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import read  # noqa: E402

GRACE = 5.0  # 공격 종료 후 맞은 경보로 인정하는 여유(초) — data-format 4장


def _load(run_dir: Path, name: str) -> list:
    f = run_dir / name
    return list(read(f)) if f.exists() else []


def _in_attack(ts: float, labels: list) -> dict | None:
    for lab in labels:
        if lab["start_ts"] <= ts <= lab["end_ts"] + GRACE:
            return lab
    return None


def classify_alert(a: dict, labels: list) -> tuple[str, dict | None]:
    """경보를 (tp|fp, 맞은 label 또는 None)으로 분류."""
    lab = _in_attack(a["ts"], labels)
    if lab is None or lab["attack"] != a["attack"]:
        # 같은 시각에 다른 공격의 label이 있을 수 있으니 attack까지 맞는 것으로 다시 확인
        lab = next((l for l in labels if l["attack"] == a["attack"]
                    and l["start_ts"] <= a["ts"] <= l["end_ts"] + GRACE), None)
    if lab is None:
        return "fp", None
    amac, lmac = a["attacker"]["mac"], lab["attacker"]["mac"]
    if lmac and amac and amac != lmac:
        return "fp", None          # 공격자 오지정 → 틀린 경보
    return "tp", lab


def evaluate_run(run_dir: Path) -> dict:
    labels = _load(run_dir, "labels.jsonl")
    actions = _load(run_dir, "actions.jsonl")
    feats = _load(run_dir, "features_1s.jsonl") + _load(run_dir, "features_5s.jsonl")
    alerts = []
    for name in ("alerts.jsonl", "alerts_rule.jsonl", "alerts_ai.jsonl"):
        alerts += _load(run_dir, name)

    # detector 집합 (경보가 없으면 'rule'로 가정해 표에 한 줄은 나오게)
    detectors = sorted({a.get("detector", "rule") for a in alerts}) or ["rule"]

    # 정상 창 수(오탐률 분모): 공격 밖에 있는 feature 창
    normal_wins = [f for f in feats if _in_attack(f["ts"], labels) is None]
    normal_win_ts = {(f["ts"], f["win"]) for f in normal_wins}

    per_det = {}
    for det in detectors:
        das = [a for a in alerts if a.get("detector", "rule") == det]
        tp = [a for a in das if classify_alert(a, labels)[0] == "tp"]
        fp = [a for a in das if classify_alert(a, labels)[0] == "fp"]
        # 공격별 탐지/시간
        detected = 0
        det_times, resp_times, attrib = [], [], []
        for lab in labels:
            mine = [a for a in tp if classify_alert(a, labels)[1] is lab or
                    (a["attack"] == lab["attack"] and
                     lab["start_ts"] <= a["ts"] <= lab["end_ts"] + GRACE)]
            if not mine:
                continue
            detected += 1
            first = min(a["ts"] for a in mine)
            det_times.append(first - lab["start_ts"])
            # 공격자 특정 여부
            attrib.append(any(a["attacker"]["mac"] == lab["attacker"]["mac"]
                              for a in mine) if lab["attacker"]["mac"] else True)
            # 대응 시간: 이 공격 구간의 첫 block
            blocks = [x for x in actions if x["action"] == "block"
                      and lab["start_ts"] <= x["ts"] <= lab["end_ts"] + GRACE]
            if blocks:
                resp_times.append(min(x["ts"] for x in blocks) - lab["start_ts"])
        fp_norm = [a for a in fp if (a["ts"], a["win"]) in normal_win_ts or
                   _in_attack(a["ts"], labels) is None]
        per_det[det] = {
            "alerts": len(das), "tp": len(tp), "fp": len(fp),
            "detected": detected, "attacks": len(labels),
            "det_time": (sum(det_times) / len(det_times)) if det_times else None,
            "resp_time": (sum(resp_times) / len(resp_times)) if resp_times else None,
            "attributed": all(attrib) if attrib else None,
            "fp_normal": len(fp_norm),
        }
    return {"run": run_dir.name, "attacks": [l["attack"] for l in labels],
            "normal_wins": len(normal_wins), "per_det": per_det}


def render(results: list) -> str:
    lines = []
    lines.append("# 탐지 성능 요약\n")
    lines.append(f"- 실험 수: {len(results)}")
    lines.append(f"- 맞은 경보 인정 여유(GRACE): {GRACE:.0f}초\n")
    lines.append("| 실험 | 공격 | 탐지기 | 탐지 | 경보 | TP | FP | 탐지시간(s) | 대응시간(s) | 공격자특정 | 정상구간오탐 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        atk = ",".join(r["attacks"]) or "-"
        for det, m in r["per_det"].items():
            dt = f"{m['det_time']:.2f}" if m["det_time"] is not None else "-"
            rt = f"{m['resp_time']:.2f}" if m["resp_time"] is not None else "-"
            at = {True: "O", False: "X", None: "-"}[m["attributed"]]
            det_s = f"{m['detected']}/{m['attacks']}"
            lines.append(f"| {r['run'][:19]} | {atk} | {det} | {det_s} | "
                         f"{m['alerts']} | {m['tp']} | {m['fp']} | {dt} | {rt} | "
                         f"{at} | {m['fp_normal']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="탐지 성능 평가 (P5)")
    p.add_argument("run_dirs", nargs="*")
    p.add_argument("--all", action="store_true", help="data/runs 전체")
    p.add_argument("--out", help="요약표를 저장할 .md 경로")
    a = p.parse_args()

    dirs = [Path(d) for d in a.run_dirs]
    if a.all:
        dirs += sorted((ROOT / "data" / "runs").glob("*/"))
    dirs = [d for d in dirs if (d / "labels.jsonl").exists()]
    if not dirs:
        sys.exit("평가할 실험 폴더가 없습니다 (labels.jsonl 필요).")

    results = [evaluate_run(d) for d in dirs]
    table = render(results)
    print(table)
    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(table, encoding="utf-8")
        print(f"[eval] 저장: {out}")


if __name__ == "__main__":
    main()
