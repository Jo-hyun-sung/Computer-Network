"""대시보드·알림이 쓰는 데이터 로딩 (P5, Streamlit 불필요).

실험 폴더에서 meta / labels / alerts(규칙·AI) / actions 를 읽어
대시보드와 디스코드 알림이 공통으로 쓰는 형태로 정리합니다.
Streamlit에 의존하지 않으므로 그대로 테스트할 수 있습니다.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import read  # noqa: E402

ALERT_FILES = ("alerts.jsonl", "alerts_rule.jsonl", "alerts_ai.jsonl")


def _load(run_dir: Path, name: str) -> list:
    f = run_dir / name
    return list(read(f)) if f.exists() else []


def load_meta(run_dir: Path) -> dict:
    import json
    f = run_dir / "meta.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def load_alerts(run_dir: Path) -> list:
    """모든 탐지기의 경보를 시각순으로. 각 경보에 읽기 좋은 필드 보강."""
    alerts = []
    for name in ALERT_FILES:
        alerts += _load(run_dir, name)
    alerts.sort(key=lambda a: a["ts"])
    return alerts


def list_runs(base: Path | None = None) -> list:
    base = base or (ROOT / "data" / "runs")
    return sorted((d for d in base.glob("*/") if (d / "meta.json").exists()),
                  key=lambda d: d.name, reverse=True)


def summarize(run_dir: Path) -> dict:
    """한 실험의 요약: 경보 수, 탐지기별 집계, 공격 목록."""
    meta = load_meta(run_dir)
    labels = _load(run_dir, "labels.jsonl")
    alerts = load_alerts(run_dir)
    actions = _load(run_dir, "actions.jsonl")
    by_det: dict[str, int] = {}
    for a in alerts:
        by_det[a.get("detector", "rule")] = by_det.get(a.get("detector", "rule"), 0) + 1
    return {
        "run_id": run_dir.name,
        "scenario": meta.get("scenario", "-"),
        "attacks": [l["attack"] for l in labels],
        "n_alerts": len(alerts),
        "by_detector": by_det,
        "n_actions": len(actions),
        "hosts": meta.get("hosts", []),
    }


def alert_rows(run_dir: Path) -> list[dict]:
    """경보를 표에 바로 쓸 수 있는 행(dict)으로 변환."""
    rows = []
    for a in load_alerts(run_dir):
        atk = a.get("attacker") or {}
        rows.append({
            "시각": round(a["ts"], 2),
            "탐지기": a.get("detector", "rule"),
            "공격": a["attack"],
            "확신도": a.get("score"),
            "공격자MAC": atk.get("mac") or "-",
            "포트": atk.get("port"),
            "근거": a.get("summary", ""),
            "규칙/모델": a.get("source", ""),
        })
    return rows
