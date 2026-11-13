"""격리 환경 안전장치.

모든 공격 스크립트는 맨 처음 `require_lab()`을 호출합니다.
Mininet 가상 호스트(별도 네트워크 네임스페이스) 안이 아니면 실행을 거부합니다.
실수로 실제 LAN(학교망, 공용 와이파이)에서 돌아가는 것을 코드로 막습니다.

판정: 현재 프로세스의 네트워크 네임스페이스가 PID 1(루트 네임스페이스)과 다른지 봅니다.
Mininet 호스트는 자기만의 네임스페이스를 가지므로 PID 1과 다릅니다.
추가로 run.py가 넘기는 LAB_OK=1 환경변수도 요구합니다.
"""

from __future__ import annotations

import os
import sys

LAB_ENV = "LAB_OK"


def in_mininet_netns() -> bool:
    """루트 네트워크 네임스페이스가 아니면 True (= Mininet 호스트 안)."""
    try:
        return os.readlink("/proc/self/ns/net") != os.readlink("/proc/1/ns/net")
    except OSError:
        return False


def require_lab() -> None:
    reasons = []
    if os.environ.get(LAB_ENV) != "1":
        reasons.append(f"{LAB_ENV}=1 환경변수가 없음 (run.py가 자동으로 설정함)")
    if not in_mininet_netns():
        reasons.append("Mininet 가상 호스트 네임스페이스가 아님 (실제 LAN일 수 있음)")
    if reasons:
        print("거부: 격리된 실험 환경에서만 실행할 수 있습니다.", file=sys.stderr)
        for r in reasons:
            print(f"  - {r}", file=sys.stderr)
        print("실행 방법: python env/run.py <시나리오> (README 참고)", file=sys.stderr)
        sys.exit(3)
