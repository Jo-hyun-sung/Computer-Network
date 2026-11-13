"""정상 트래픽 발생기 — Mininet 호스트 안에서 역할별로 실행.

run.py가 각 호스트에서 이 스크립트를 띄웁니다.

  - gateway/dhcp 서버: iperf3 서버, 간단한 HTTP 서버를 띄워 둠
  - client: 주기적으로 ping(ARP 유발), HTTP 내려받기(TCP), DNS 조회를 섞어서 보냄

탐지기의 오탐을 확인하려면 "정상인데 공격처럼 보이는" 트래픽도 필요합니다.
그래서 클라이언트는 여러 목적지로 고르게 접속합니다(한 곳만 때리지 않음).
"""

from __future__ import annotations

import argparse
import random
import subprocess
import time

from env.hosts import GATEWAY_IP, by_role


def _run(cmd: str, timeout: float | None = None) -> None:
    try:
        subprocess.run(cmd, shell=True, timeout=timeout,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass


def server(duration: float, http_port: int) -> None:
    """서버 역할(gateway): iperf3 서버 + HTTP 서버를 duration 동안 띄움."""
    procs = [
        subprocess.Popen(["iperf3", "-s", "-1"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL),
        subprocess.Popen(["python3", "-m", "http.server", str(http_port)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
    ]
    try:
        time.sleep(duration)
    finally:
        for p in procs:
            p.terminate()


def client(duration: float, http_port: int, seed: int) -> None:
    """클라이언트 역할: ping / HTTP / DNS 를 섞어서 반복."""
    rnd = random.Random(seed)
    # 접속할 정상 상대 목록 (자기 자신 제외)
    peers = [h.ip for h in by_role("client") + by_role("gateway")]
    end = time.time() + duration
    while time.time() < end:
        kind = rnd.choice(["ping", "ping", "http", "dns"])
        if kind == "ping":
            dst = rnd.choice(peers)
            _run(f"ping -c {rnd.randint(1, 3)} -W 1 {dst}", timeout=5)
        elif kind == "http":
            _run(f"wget -q -O /dev/null http://{GATEWAY_IP}:{http_port}/", timeout=5)
        else:  # dns: 게이트웨이의 dnsmasq에 조회
            name = rnd.choice(["a", "b", "c", "www"]) + ".lab.test"
            _run(f"nslookup {name} {GATEWAY_IP}", timeout=5)
        time.sleep(rnd.uniform(0.3, 1.5))


def main() -> None:
    p = argparse.ArgumentParser(description="정상 트래픽 발생기")
    p.add_argument("--role", required=True, choices=["server", "client"])
    p.add_argument("--duration", type=float, default=60.0)
    p.add_argument("--http-port", type=int, default=8000)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    if a.role == "server":
        server(a.duration, a.http_port)
    else:
        client(a.duration, a.http_port, a.seed)


if __name__ == "__main__":
    main()
