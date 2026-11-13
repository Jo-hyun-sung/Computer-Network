"""시나리오 정의 — 어떤 공격을, 누가, 어떤 설정으로.

run.py가 이 정의를 읽어서 (1) 공격 스크립트를 공격자 호스트에서 실행하고
(2) data-format.md의 label 기록을 만듭니다. label의 attacker/target/evasive/params가
여기서 나옵니다.

10주차 목표는 arp_spoof 와 mac_flood 입니다. 나머지 공격은 11주차에 채웁니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from env.hosts import GATEWAY_IP, by_name


@dataclass
class Scenario:
    name: str
    attack: str                      # data-format.md의 공격 종류
    attacker: str                    # 호스트 이름
    module: str                      # python -m 로 실행할 공격 모듈
    args: list[str]                  # 공격 스크립트 인자 (iface는 run.py가 채움)
    target: str | None = None        # 피해자 호스트 이름 (없으면 None)
    evasive: bool = False
    params: dict = field(default_factory=dict)
    warmup: float = 10.0             # 공격 전 정상 트래픽만 흐르는 시간(초)
    attack_dur: float = 30.0         # 공격 지속 시간(초)
    cooldown: float = 5.0            # 공격 후 정상 트래픽 시간(초)

    @property
    def duration(self) -> float:
        return self.warmup + self.attack_dur + self.cooldown


SCENARIOS: dict[str, Scenario] = {
    # ARP 스푸핑: h4가 게이트웨이(10.0.0.254)를 사칭, 피해자 h1
    "arp_spoof": Scenario(
        name="arp_spoof", attack="arp_spoof", attacker="h4", target="h1",
        module="env.attacks.arp_spoof",
        args=["--spoof-ip", GATEWAY_IP, "--victim-ip", "10.0.0.1", "--rate", "2"],
        params={"tool": "scapy", "rate_pps": 2, "spoofed_ip": GATEWAY_IP},
    ),
    # 느린 ARP 스푸핑(회피): 초당 0.2개로 아주 천천히 — 규칙 임계치를 피하려는 공격
    "arp_spoof_slow": Scenario(
        name="arp_spoof_slow", attack="arp_spoof", attacker="h4", target="h1",
        module="env.attacks.arp_spoof",
        args=["--spoof-ip", GATEWAY_IP, "--victim-ip", "10.0.0.1", "--rate", "0.2"],
        evasive=True, attack_dur=60.0,
        params={"tool": "scapy", "rate_pps": 0.2, "spoofed_ip": GATEWAY_IP, "evasion": "low-rate"},
    ),
    # MAC 플러딩: h4가 가짜 출발지 MAC을 대량 전송 (대상 없음)
    "mac_flood": Scenario(
        name="mac_flood", attack="mac_flood", attacker="h4", target=None,
        module="env.attacks.mac_flood",
        args=["--rate", "500"], attack_dur=20.0,
        params={"tool": "scapy", "rate_fps": 500},
    ),
}


def get(name: str) -> Scenario:
    if name not in SCENARIOS:
        raise KeyError(f"없는 시나리오: {name}. 가능: {sorted(SCENARIOS)}")
    return SCENARIOS[name]
