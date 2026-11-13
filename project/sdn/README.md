# sdn/ — SDN 컨트롤러와 자동 차단 (P4)

Mininet 스위치를 OS-Ken(SDN 컨트롤러)이 제어하게 합니다. 10주차는 **기본 L2 스위치 제어**까지,
12주차에 **경보가 오면 공격자 포트/MAC을 자동 차단**하도록 확장합니다.

> Ryu는 Python 3.8~3.9가 필요해 설치가 까다로워, 후속작인 **OS-Ken**을 씁니다
> (`apt install python3-os-ken`, 추가 Python 불필요).

## 파일

| 파일 | 내용 |
|---|---|
| `l2_switch.py` | OS-Ken L2 학습 스위치 (OpenFlow 1.3). 자동 차단의 토대 |

## 실행

터미널 2개가 필요합니다.

```bash
# 1) 컨트롤러 (project 폴더에서)
PYTHONPATH=$PWD osken-manager sdn.l2_switch        # 127.0.0.1:6653 대기

# 2) 실험 (다른 터미널)
sudo python3 env/run.py arp_spoof --controller remote
```

`--controller remote`면 run.py가 스위치를 OpenFlow 1.3으로 맞춰 OS-Ken에 연결합니다.

## 검증 상태 (2026-11-13, 실제 실행)

- ✅ **OS-Ken이 스위치를 실제로 제어함을 확정**: `failMode=secure`(OVS 자체 스위칭 금지)에서
  pingall 0% 손실. 컨트롤러가 흐름을 설치하지 않으면 불가능한 결과.
- ✅ 컨트롤러 로그: "switch 1 연결됨"(table-miss 설치) + PacketIn 이벤트 처리 확인
- ✅ `run.py --controller remote`로 arp_spoof 실험 정상 동작(캡처·탐지까지)

## 다음 단계 (12주차)

- 경보(`alerts_*.jsonl`)를 받으면 공격자 MAC/포트에 **drop 흐름 규칙 설치**(사후 차단)
- ★ 사전 차단: DHCP 응답으로 IP-MAC-포트 표를 만들고, 표와 안 맞는 ARP를 미리 버림
- 차단 후 `action` 기록(data-format 2.5)을 남겨 대응 시간 측정(P5)
