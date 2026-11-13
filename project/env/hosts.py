"""실험망 호스트 정의 — 단 하나의 기준 (single source of truth).

Mininet 토폴로지(topo.py)와 meta.json(run.py)을 모두 이 목록에서 만듭니다.
MAC·IP·포트를 두 곳에 따로 적으면 반드시 어긋나므로, 바꿀 때는 여기만 고칩니다.

포트 번호 = 스위치 s1의 포트 = s1-eth<port>. data-format.md의 endpoint와 같은 의미.
"""

from __future__ import annotations

from dataclasses import dataclass

SWITCH = "s1"
SUBNET = "10.0.0.0/24"
PREFIX = 24


@dataclass(frozen=True)
class HostSpec:
    name: str       # Mininet 호스트 이름 (h1, gw, ...)
    role: str       # client / gateway / dhcp_server / attacker
    mac: str        # 소문자 콜론 (data-format.md 규칙)
    ip: str         # 10.0.0.X
    port: int       # s1-eth<port>

    def endpoint(self) -> dict:
        return {"mac": self.mac, "ip": self.ip, "sw": SWITCH, "port": self.port}


# 스위치 1대 + 정상 PC 3대 + 게이트웨이 + DHCP 서버 + 공격자 1대
HOSTS: list[HostSpec] = [
    HostSpec("h1",   "client",      "00:00:00:00:00:01", "10.0.0.1",   1),
    HostSpec("h2",   "client",      "00:00:00:00:00:02", "10.0.0.2",   2),
    HostSpec("h3",   "client",      "00:00:00:00:00:03", "10.0.0.3",   3),
    HostSpec("h4",   "attacker",    "00:00:00:00:00:04", "10.0.0.4",   4),
    HostSpec("gw",   "gateway",     "00:00:00:00:00:fe", "10.0.0.254", 5),
    HostSpec("dhcp", "dhcp_server", "00:00:00:00:00:fd", "10.0.0.253", 6),
]

GATEWAY_IP = "10.0.0.254"


def by_name(name: str) -> HostSpec:
    for h in HOSTS:
        if h.name == name:
            return h
    raise KeyError(f"없는 호스트: {name}")


def by_role(role: str) -> list[HostSpec]:
    return [h for h in HOSTS if h.role == role]


def one(role: str) -> HostSpec:
    hs = by_role(role)
    if len(hs) != 1:
        raise ValueError(f"{role} 역할 호스트가 {len(hs)}개 (1개여야 함)")
    return hs[0]
