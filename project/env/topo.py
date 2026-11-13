"""Mininet 토폴로지: 스위치 1대에 hosts.py의 호스트를 모두 연결.

실제 사용은 run.py가 `Mininet(topo=LanTopo(), ...)`로 띄웁니다.
(`mn --custom --topo lan` CLI는 mn 내부 처리와 충돌해 쓰지 않습니다. run.py를 쓰세요.)
"""

from __future__ import annotations

from mininet.topo import Topo

try:
    from env.hosts import HOSTS, PREFIX, SWITCH
except ModuleNotFoundError:
    # `mn --custom env/topo.py`로 로드되면 env 패키지가 경로에 없음.
    # (이때 mn은 __file__을 정의하지 않으므로 현재 폴더(project/)를 경로에 추가)
    import sys
    sys.path.insert(0, ".")
    from env.hosts import HOSTS, PREFIX, SWITCH


class LanTopo(Topo):
    """hosts.py 정의대로 스위치 s1에 호스트를 붙입니다.

    MAC과 스위치 포트 번호를 hosts.py 값으로 고정하므로,
    캡처에서 본 포트가 meta.json의 포트와 항상 일치합니다.
    """

    def build(self) -> None:
        sw = self.addSwitch(SWITCH)
        for h in HOSTS:
            node = self.addHost(h.name, ip=f"{h.ip}/{PREFIX}", mac=h.mac)
            # port2 = 스위치 쪽 포트 번호 → s1-eth<port>
            self.addLink(node, sw, port2=h.port)


# `mn --custom ... --topo lan`에서 쓰는 이름
topos = {"lan": LanTopo}
