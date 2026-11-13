"""규칙 기반 탐지기 (P4).

실험 폴더의 features_1s.jsonl / features_5s.jsonl 을 읽어 공격을 판정하고
alerts_rule.jsonl 을 만듭니다. 형식은 docs/data-format.md 2.4.

    python3 rules/detect.py data/runs/<run_id>

10주차 규칙(2종):
  R1 arp_conflict   : feat_host.arp_ip_conflicts > 0  → ARP 스푸핑
                      (학습된 IP-MAC 대응표와 다른 MAC이 그 IP를 주장)
  R2 arp_unsolicited: feat_host.arp_rep_unsolicited ≥ 임계치(5초창) → ARP 스푸핑
                      (R1이 못 잡는 느린/변형 경우 보강)
  R3 mac_flood      : feat_seg.new_src_macs ≥ 임계치(1초창) → MAC 플러딩

같은 (공격자, 공격)은 10초에 한 번만 경보(data-format 2.4). 임계치는 상단 상수.
11주차에 DHCP·스캔·SYN flood 규칙을 추가합니다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import make, read, write  # noqa: E402

# 임계치 (팀 회의에서 조정 가능)
ARP_UNSOLICITED_MIN = 5      # 5초 창에서 미요청 ARP 응답 몇 개부터 의심
# 1초 창에서 새 출발지 MAC 몇 개부터 플러딩으로 볼지.
# 실험망 정상 호스트는 6대뿐이라, 1초에 새 MAC 15개는 명백한 비정상.
MAC_FLOOD_NEW_MACS = 15
DEDUP_SEC = 10.0             # 같은 공격자·공격 경보 묶는 시간


class Deduper:
    def __init__(self, window: float = DEDUP_SEC):
        self.window = window
        self.last: dict[tuple, float] = {}

    def allow(self, key: tuple, ts: float) -> bool:
        prev = self.last.get(key)
        if prev is not None and ts - prev < self.window:
            return False
        self.last[key] = ts
        return True


def detect(run_dir: Path) -> None:
    feats = []
    for w in (1, 5):
        f = run_dir / f"features_{w}s.jsonl"
        if f.exists():
            feats += list(read(f))
    if not feats:
        sys.exit(f"특징 파일 없음: {run_dir} (먼저 capture/extract.py 실행)")
    feats.sort(key=lambda r: r["ts"])

    dedup = Deduper()
    n = 0
    out = run_dir / "alerts_rule.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for r in feats:
            alert = None
            if r["type"] == "feat_host":
                host = r["host"]
                # R1: ARP 충돌
                if r["arp_ip_conflicts"] > 0:
                    if dedup.allow(("arp_spoof", host["mac"]), r["ts"]):
                        alert = _mk(r, host, "arp_conflict", score=1.0,
                                    summary=f"{host['mac']}가 다른 호스트의 IP를 사칭(ARP 충돌)",
                                    evidence={"arp_ip_conflicts": r["arp_ip_conflicts"],
                                              "arp_rep_unsolicited": r["arp_rep_unsolicited"]})
                # R2: 미요청 ARP 응답 다발 (5초 창)
                elif r["win"] == 5 and r["arp_rep_unsolicited"] >= ARP_UNSOLICITED_MIN:
                    if dedup.allow(("arp_spoof", host["mac"]), r["ts"]):
                        alert = _mk(r, host, "arp_unsolicited", score=0.8,
                                    summary=f"{host['mac']}가 요청 없는 ARP 응답을 {r['arp_rep_unsolicited']}회 전송",
                                    evidence={"arp_rep_unsolicited": r["arp_rep_unsolicited"]})
            elif r["type"] == "feat_seg":
                # R3: MAC 플러딩 (1초 창, 구간별 새 MAC 급증)
                if r["win"] == 1 and r["new_src_macs"] >= MAC_FLOOD_NEW_MACS:
                    seg = {"mac": None, "ip": None, "sw": r["sw"], "port": r["port"]}
                    key = ("mac_flood", r["sw"], r["port"])
                    if dedup.allow(key, r["ts"]):
                        alert = _mk(r, seg, "mac_flood", attack="mac_flood", score=1.0,
                                    summary=f"구간(sw={r['sw']},port={r['port']})에서 새 MAC {r['new_src_macs']}개 급증(MAC 플러딩)",
                                    evidence={"new_src_macs": r["new_src_macs"],
                                              "src_macs": r["src_macs"]})
            if alert:
                write(fh, alert)
                n += 1
    print(f"[detect] {out.name}: 경보 {n}개")


_SEQ = [0]


def _mk(feat, attacker, source, *, attack="arp_spoof", score, summary, evidence):
    _SEQ[0] += 1
    # 오프라인: 경보 시각 = 근거 특징 창이 끝난 시각(실시간이라면 그때 판정됨).
    # make()의 기본값(현재 벽시계)을 쓰면 캡처 시점과 어긋나므로 반드시 지정.
    return make("alert", ts=feat["ts"], alert_id=f"rule-{_SEQ[0]:06d}",
                detector="rule", source=source, attack=attack, score=score,
                attacker=attacker, victim=None, feature_ts=feat["ts"],
                win=feat["win"], summary=summary, evidence=evidence)


def main() -> None:
    p = argparse.ArgumentParser(description="규칙 기반 탐지기 (P4)")
    p.add_argument("run_dir")
    a = p.parse_args()
    detect(Path(a.run_dir))


if __name__ == "__main__":
    main()
