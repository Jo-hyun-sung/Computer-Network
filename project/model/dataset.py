"""실험 폴더들의 feat_host 기록 → 학습용 (X, y) 데이터셋 (P3).

라벨 붙이는 법:
  feat_host 기록의 시각이 어떤 공격 구간 안이고, 그 기록의 host.mac이
  공격자 MAC과 같으면 → 그 공격 이름, 아니면 → "normal".

주의: MAC 플러딩·DHCP 고갈은 공격자가 매번 '가짜 MAC'을 쓰므로 feat_host(진짜 MAC 기준)
  로는 공격자가 드러나지 않습니다. 그래서 이 데이터셋(호스트 단위)은 호스트에 귀속되는
  공격(arp_spoof 등)용입니다. 플러딩류는 feat_seg 기반 모델/규칙에서 다룹니다.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import read  # noqa: E402

# 학습에 쓰는 feat_host 숫자 특징 (신원/시각 제외)
FEATURES = [
    "win", "pkts", "bytes", "arp_req", "arp_rep", "arp_grat",
    "arp_rep_unsolicited", "arp_ip_claims", "arp_ip_conflicts",
    "dhcp_offer", "dhcp_ack", "dhcp_discover", "tcp_syn", "tcp_synack_in",
    "tcp_rst_in", "icmp_unreach_in", "dst_ips", "dst_ports",
    "top_dst_share", "dns_resp",
]

# feat_host(진짜 출발지 MAC)로 공격자를 특정할 수 있는 공격만 호스트 라벨로 사용
HOST_ATTRIBUTABLE = {"arp_spoof", "dns_spoof", "port_scan", "syn_flood", "dhcp_rogue"}


def _labels(run_dir: Path) -> list:
    f = run_dir / "labels.jsonl"
    return list(read(f)) if f.exists() else []


def label_for(rec: dict, labels: list) -> str:
    mac = rec["host"]["mac"]
    for lab in labels:
        if (lab["attack"] in HOST_ATTRIBUTABLE
                and lab["start_ts"] <= rec["ts"] <= lab["end_ts"]
                and lab["attacker"]["mac"] == mac):
            return lab["attack"]
    return "normal"


def rows_from_run(run_dir: Path):
    """(feature_dict, label, meta) 들을 돌려줍니다."""
    labels = _labels(run_dir)
    out = []
    for w in (1, 5):
        f = run_dir / f"features_{w}s.jsonl"
        if not f.exists():
            continue
        for rec in read(f):
            if rec.get("type") != "feat_host":
                continue
            y = label_for(rec, labels)
            out.append((rec, y, run_dir.name))
    return out


def build(run_dirs):
    """여러 실험 폴더 → (X, y, meta). X는 리스트(행)×FEATURES 순서."""
    X, y, meta = [], [], []
    for d in run_dirs:
        d = Path(d)
        for rec, lab, run in rows_from_run(d):
            X.append([float(rec.get(k, 0) or 0) for k in FEATURES])
            y.append(lab)
            meta.append({"run": run, "ts": rec["ts"], "mac": rec["host"]["mac"],
                         "win": rec["win"]})
    return X, y, meta


def all_runs() -> list:
    base = ROOT / "data" / "runs"
    return [d for d in sorted(base.glob("*/"))
            if (d / "features_1s.jsonl").exists() or (d / "features_5s.jsonl").exists()]
