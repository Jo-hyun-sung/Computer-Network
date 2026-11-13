# env/ — 실험 환경과 공격·정상 트래픽 (P1)

격리된 Mininet LAN을 띄우고, 정상 트래픽과 공격을 재현해서 `data/runs/<run_id>/`에
캡처(`capture.pcap`), 정답(`labels.jsonl`), 실험 정보(`meta.json`)를 남깁니다.
형식은 [`../docs/data-format.md`](../docs/data-format.md)를 따릅니다.

## 안전 수칙 (반드시)

- **격리된 Mininet 환경에서만** 실행합니다. 공격 스크립트는 실제 LAN(학교망, 공용 와이파이)에서
  실행되지 않도록 `attacks/labguard.py`가 코드로 막습니다(Mininet 네임스페이스 + `LAB_OK=1` 확인).
- Mininet 가상 MAC(`00:00:00:00:00:0X`)만 씁니다.

## 필요 환경 (WSL2 Ubuntu 24.04 기준, 설치 완료)

```
sudo apt install mininet openvswitch-switch python3-scapy \
     dsniff hping3 nmap tcpdump iperf3 dnsmasq-base dnsutils
```
- Mininet은 Linux 전용입니다. Windows에서는 WSL2 또는 Ubuntu VM 안에서 실행합니다.
- root 권한이 필요합니다(`sudo`).

## 실행

```bash
# project/ 폴더에서
sudo python3 env/run.py arp_spoof          # ARP 스푸핑 시나리오
sudo python3 env/run.py mac_flood          # MAC 플러딩
sudo python3 env/run.py arp_spoof_slow     # 느린 ARP 스푸핑(회피 공격)
sudo python3 env/run.py arp_spoof --no-pcap        # 캡처 생략(빠름)
sudo python3 env/run.py arp_spoof --controller remote  # OS-Ken 붙일 때(P4)

# 결과 검사
python3 common/records.py check data/runs/<run_id>
```

각 실험은 `워밍업 → 공격 → 쿨다운` 순서로 진행합니다(시간은 `scenarios.py`에서 조정).

## 구성 파일

| 파일 | 내용 |
|---|---|
| `hosts.py` | **호스트 정의(단일 기준).** MAC·IP·포트를 여기만 고치면 토폴로지와 meta.json에 함께 반영됨 |
| `topo.py` | Mininet 토폴로지(스위치 1대 + 호스트 6대) |
| `scenarios.py` | 시나리오 정의(공격자, 대상, 속도, 회피 여부 → label에 반영) |
| `run.py` | 실험 실행기: 망 구성 → meta.json → 캡처 → 정상 트래픽 → 공격 → labels.jsonl |
| `traffic/normal.py` | 정상 트래픽(ping, HTTP, DNS) |
| `attacks/arp_spoof.py` | ARP 스푸핑 (w07) |
| `attacks/mac_flood.py` | MAC 플러딩 (w07) |
| `attacks/labguard.py` | 격리 환경 안전장치 |

## 토폴로지

```
  h1(10.0.0.1)  h2(10.0.0.2)  h3(10.0.0.3)  h4(10.0.0.4, 공격자)
      │p1           │p2            │p3            │p4
      └─────────────┴──────[ s1 ]──┴─────────────┘
                           │p5          │p6
                      gw(10.0.0.254)  dhcp(10.0.0.253)
```

## 검증 상태 (2026-11-13, WSL2에서 실제 실행)

- ✅ 6호스트 토폴로지가 run.py로 정상 구성됨(정상 트래픽 ping·HTTP 상호 통신 확인)
- ✅ `arp_spoof`: 캡처에 공격자(`...04`)와 게이트웨이(`...fe`)가 둘 다 `10.0.0.254`를
  주장하는 ARP 충돌이 찍힘 → 규칙 탐지기의 핵심 근거. meta/labels 형식 검사 통과
- ✅ `mac_flood`: 짧은 시간에 서로 다른 출발지 MAC 171개 관측 → `feat_seg` 신호
- ✅ 안전장치: Mininet 밖에서 공격 스크립트 직접 실행 시 거부(종료코드 3)

## 알려진 한계 (다음 주 보완)

- ✅ **정상 DNS 트래픽 캡처됨** (`dnsutils` 설치 후 확인, `*.lab.test` 질의·응답). ping·HTTP·DNS 혼합.
- **MAC 플러딩 실제 전송 속도는 설정값보다 낮음**(scapy 파이썬 루프 한계, ~수백 pps).
  CAM 테이블을 실제로 넘치게 하려면 `tcpreplay`/`sendpfast`로 교체 가능하나,
  *탐지*에는 "짧은 시간 내 다수의 새 MAC"만으로 충분함.
- 아직 P2(캡처→특징)·P4(규칙) 모듈과 연결 전. pcap은 만들어지므로 오프라인 입력으로 바로 쓸 수 있음.
