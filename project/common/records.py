"""모듈 간 기록 형식(docs/data-format.md v1)의 공용 도구.

표준 라이브러리만 사용합니다. 모든 모듈이 이 파일을 가져다 씁니다.

    from common.records import make, write, read, validate

    rec = make("alert", alert_id="rule-000001", detector="rule", ...)
    with open("alerts.jsonl", "a", encoding="utf-8") as fh:
        write(fh, rec)

명령줄 검사:

    python common/records.py check data/runs/<run_id>/alerts.jsonl
    python common/records.py check data/runs/<run_id>          # 폴더 안 .jsonl 전부
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterator, TextIO

VERSION = 1

ATTACKS = {
    "normal", "arp_spoof", "mac_flood", "dhcp_rogue",
    "dhcp_starve", "port_scan", "syn_flood", "dns_spoof",
}

NUM = (int, float)
OPT = type(None)
COMMON_FIELDS = ("v", "type", "ts")
_MAC_RE = re.compile(r"^[0-9a-f]{2}(:[0-9a-f]{2}){5}$")
# "PowerShell Out-File"은 UTF-8 BOM을 붙이므로 utf-8-sig로 읽습니다.
_READ_ENCODING = "utf-8-sig"

# 필드 이름 → 허용 타입. "endpoint"와 "attack"은 따로 검사합니다.
_ENDPOINT = "endpoint"
_ENDPOINT_OPT = "endpoint?"
_ATTACK = "attack"

_COUNTS_HOST = [
    "pkts", "bytes", "arp_req", "arp_rep", "arp_grat", "arp_rep_unsolicited",
    "arp_ip_claims", "arp_ip_conflicts", "dhcp_offer", "dhcp_ack",
    "dhcp_discover", "tcp_syn", "tcp_synack_in", "tcp_rst_in",
    "icmp_unreach_in", "dst_ips", "dst_ports", "dns_resp",
]
_COUNTS_SEG = [
    "pkts", "bytes", "src_macs", "new_src_macs", "dhcp_discover",
    "dhcp_chaddrs", "dhcp_offer", "dhcp_servers", "arp_rep", "tcp_syn",
]

SCHEMAS: dict[str, dict[str, Any]] = {
    "label": {
        "attack_id": str, "attack": _ATTACK, "start_ts": NUM, "end_ts": NUM,
        "attacker": _ENDPOINT, "target": _ENDPOINT_OPT, "evasive": bool,
        "params": dict,
    },
    "feat_host": {
        "win": int, "host": _ENDPOINT, "top_dst_share": NUM, "extra": dict,
        **{k: int for k in _COUNTS_HOST},
    },
    "feat_seg": {
        "win": int, "sw": (str, OPT), "port": (int, OPT), "extra": dict,
        **{k: int for k in _COUNTS_SEG},
    },
    "alert": {
        "alert_id": str, "detector": ("rule", "ai", "hybrid"), "source": str,
        "attack": _ATTACK, "score": NUM, "attacker": _ENDPOINT,
        "victim": _ENDPOINT_OPT, "feature_ts": NUM, "win": int,
        "summary": str, "evidence": dict,
    },
    "action": {
        "action": ("block", "unblock", "pre_drop"), "target": _ENDPOINT,
        "alert_id": (str, OPT), "reason": str, "expires_ts": (*NUM, OPT),
        "ok": bool, "install_ms": NUM,
    },
}


def now() -> float:
    """모든 모듈이 쓰는 시각 기준 (Unix epoch 초)."""
    return time.time()


def endpoint(mac: str | None = None, ip: str | None = None,
             sw: str | None = None, port: int | None = None) -> dict:
    return {"mac": mac.lower() if mac else None, "ip": ip, "sw": sw, "port": port}


def make(rtype: str, ts: float | None = None, **fields: Any) -> dict:
    """공통 필드를 채운 기록을 만들고 검사합니다. 틀리면 ValueError."""
    if rtype in ("feat_host", "feat_seg"):
        fields.setdefault("extra", {})
        for k in (_COUNTS_HOST if rtype == "feat_host" else _COUNTS_SEG):
            fields.setdefault(k, 0)
        if rtype == "feat_host":
            fields.setdefault("top_dst_share", 0.0)
    rec = {"v": VERSION, "type": rtype, "ts": now() if ts is None else ts, **fields}
    errors = validate(rec)
    if errors:
        raise ValueError(f"{rtype} 기록 형식 오류: " + "; ".join(errors))
    return rec


def write(fh: TextIO, rec: dict) -> None:
    """한 줄 쓰고 바로 flush (실시간으로 읽는 쪽이 바로 볼 수 있게)."""
    fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    fh.flush()


def read(path: str | Path) -> Iterator[dict]:
    with open(path, encoding=_READ_ENCODING) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _check_endpoint(name: str, val: Any, optional: bool) -> list[str]:
    if val is None:
        return [] if optional else [f"{name}: null이면 안 됨"]
    if not isinstance(val, dict):
        return [f"{name}: endpoint 객체여야 함"]
    errs = []
    for k, t in (("mac", str), ("ip", str), ("sw", str), ("port", int)):
        if k not in val:
            errs.append(f"{name}.{k}: 없음 (모르면 null)")
        elif val[k] is not None and (not isinstance(val[k], t) or isinstance(val[k], bool)):
            errs.append(f"{name}.{k}: {t.__name__} 또는 null이어야 함")
    extra = set(val) - {"mac", "ip", "sw", "port"}
    if extra:
        errs.append(f"{name}: 모르는 필드 {sorted(extra)}")
    mac = val.get("mac")
    if isinstance(mac, str) and not _MAC_RE.match(mac):
        errs.append(f"{name}.mac: 소문자 콜론 형식(00:00:00:00:00:04)이어야 함 ({mac})")
    return errs


def _check_epoch(name: str, val: Any) -> list[str]:
    """Unix epoch 초인지 확인 (2001~2286년). 밀리초, 상대 시각을 걸러냄."""
    if isinstance(val, bool) or not isinstance(val, NUM):
        return [f"{name}: 숫자(Unix epoch 초)여야 함"]
    if not 1e9 <= val < 1e10:
        return [f"{name}: 밀리초나 상대 시각이 아니라 epoch 초여야 함 ({val})"]
    return []


def validate(rec: Any) -> list[str]:
    """형식 오류 목록을 돌려줍니다. 빈 목록이면 통과."""
    if not isinstance(rec, dict):
        return ["기록은 JSON 객체여야 함"]
    errs = []
    if rec.get("v") != VERSION:
        errs.append(f"v: {VERSION}이어야 함")
    rtype = rec.get("type")
    if rtype not in SCHEMAS:
        return errs + [f"type: {sorted(SCHEMAS)} 중 하나여야 함 ({rtype!r})"]
    errs += _check_epoch("ts", rec.get("ts"))

    # 형식에 없는 필드는 오류 (오타가 조용히 0으로 바뀌는 것을 막음). 추가 값은 extra에.
    unknown = set(rec) - set(COMMON_FIELDS) - set(SCHEMAS[rtype])
    if unknown:
        errs.append(f"모르는 필드 {sorted(unknown)} (추가 값은 extra 안에 넣으세요)")

    for name, spec in SCHEMAS[rtype].items():
        if name not in rec:
            errs.append(f"{name}: 없음")
            continue
        val = rec[name]
        if spec == _ENDPOINT or spec == _ENDPOINT_OPT:
            errs += _check_endpoint(name, val, spec == _ENDPOINT_OPT)
        elif spec == _ATTACK:
            if val not in ATTACKS:
                errs.append(f"{name}: 알 수 없는 공격 종류 {val!r}")
        elif isinstance(spec, tuple) and spec and all(isinstance(s, str) for s in spec):
            if val not in spec:
                errs.append(f"{name}: {spec} 중 하나여야 함 ({val!r})")
        else:
            types = spec if isinstance(spec, tuple) else (spec,)
            ok = isinstance(val, types) and not (isinstance(val, bool) and bool not in types)
            if not ok:
                errs.append(f"{name}: 타입이 맞지 않음 ({type(val).__name__})")
            elif name.endswith("_ts") and val is not None:
                errs += _check_epoch(name, val)

    if rtype in ("feat_host", "feat_seg"):
        if rec.get("win") not in (1, 5):
            errs.append("win: 1 또는 5")
        counts = _COUNTS_HOST if rtype == "feat_host" else _COUNTS_SEG
        errs += [f"{k}: 음수" for k in counts if isinstance(rec.get(k), int) and rec[k] < 0]
    if rtype == "feat_host" and isinstance(rec.get("top_dst_share"), NUM):
        if not 0 <= rec["top_dst_share"] <= 1:
            errs.append("top_dst_share: 0~1")
    if rtype == "label":
        if rec.get("attack") == "normal":
            errs.append("attack: label에는 normal을 쓰지 않음")
        s, e = rec.get("start_ts"), rec.get("end_ts")
        if isinstance(s, NUM) and isinstance(e, NUM) and e < s:
            errs.append("end_ts가 start_ts보다 이름")
    if rtype == "alert" and isinstance(rec.get("score"), NUM):
        if not 0 <= rec["score"] <= 1:
            errs.append("score: 0~1")
    return errs


def check_file(path: Path) -> int:
    bad = 0
    with open(path, encoding=_READ_ENCODING) as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"{path}:{n}: JSON 오류: {e}")
                bad += 1
                continue
            for err in validate(rec):
                print(f"{path}:{n}: {err}")
                bad += 1
    return bad


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 한글 깨짐 방지
    if len(argv) < 2 or argv[0] != "check":
        print(__doc__)
        return 2
    files: list[Path] = []
    for arg in argv[1:]:
        p = Path(arg)
        if p.is_dir():
            found = sorted(p.glob("*.jsonl"))
            if not found:
                print(f"검사할 .jsonl 파일이 없음: {p}")
                return 2
            files += found
        elif p.is_file():
            files.append(p)
        else:
            print(f"파일이나 폴더가 없음: {p}")
            return 2
    total = 0
    for f in files:
        bad = check_file(f)
        total += bad
        print(f"{'통과' if bad == 0 else f'오류 {bad}개'}  {f}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
