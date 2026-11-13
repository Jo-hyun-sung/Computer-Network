"""디스코드 웹훅 알림 (P5).

경보 1건을 디스코드 메시지 형식으로 만들고, 웹훅 URL이 있으면 전송합니다.
기본은 --dry-run: 실제 전송 없이 보낼 내용을 출력합니다(외부로 아무것도 안 나감).

실제 전송:
    export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
    python3 dashboard/notify.py data/runs/<run_id> --send

웹훅 URL은 각자 디스코드 서버 설정에서 발급합니다. 저장소에 올리지 마세요.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.load import load_alerts  # noqa: E402

ENV_URL = "DISCORD_WEBHOOK_URL"


def format_alert(alert: dict) -> dict:
    """디스코드 임베드 payload로 변환."""
    atk = alert.get("attacker") or {}
    color = {"arp_spoof": 0xE74C3C, "mac_flood": 0xE67E22,
             "dhcp_rogue": 0xF1C40F}.get(alert["attack"], 0x95A5A6)
    fields = [
        {"name": "탐지기", "value": alert.get("detector", "rule"), "inline": True},
        {"name": "확신도", "value": f"{alert.get('score', 0):.0%}", "inline": True},
        {"name": "공격자",
         "value": f"{atk.get('mac') or '미상'} (port {atk.get('port')})", "inline": True},
    ]
    return {
        "username": "LAN 공격 탐지기",
        "embeds": [{
            "title": f"⚠️ {alert['attack']} 탐지",
            "description": alert.get("summary", ""),
            "color": color,
            "fields": fields,
            "footer": {"text": f"alert_id={alert.get('alert_id', '-')}"},
        }],
    }


def send(payload: dict, url: str, timeout: float = 5.0) -> int:
    import json
    import urllib.request
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


def main() -> None:
    import json
    p = argparse.ArgumentParser(description="디스코드 웹훅 알림 (P5)")
    p.add_argument("run_dir")
    p.add_argument("--send", action="store_true", help="실제 전송(기본은 미리보기)")
    p.add_argument("--max", type=int, default=3, help="보낼 경보 최대 개수")
    a = p.parse_args()

    alerts = load_alerts(Path(a.run_dir))
    if not alerts:
        print("경보가 없습니다.")
        return
    url = os.environ.get(ENV_URL)
    if a.send and not url:
        sys.exit(f"{ENV_URL} 환경변수에 웹훅 URL을 설정하세요.")

    for alert in alerts[:a.max]:
        payload = format_alert(alert)
        if a.send:
            status = send(payload, url)
            print(f"전송 {alert.get('alert_id')}: HTTP {status}")
        else:
            print("[미리보기] 전송하지 않음. payload:")
            print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
