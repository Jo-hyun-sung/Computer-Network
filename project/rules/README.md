# rules/ — 규칙 기반 탐지기 (P4)

특징(`features_*.jsonl`)을 읽어 공격을 판정하고 경보(`alerts_rule.jsonl`)를 만듭니다.
형식은 [`../docs/data-format.md`](../docs/data-format.md) 2.4.

## 사용

```bash
python3 rules/detect.py data/runs/<run_id>
# → alerts_rule.jsonl 생성
```

## 규칙 (10주차, 2종)

| 규칙 | 조건 | 판정 |
|---|---|---|
| `arp_conflict` | `feat_host.arp_ip_conflicts > 0` | ARP 스푸핑 (학습된 대응표와 다른 MAC이 IP 주장) |
| `arp_unsolicited` | `feat_host.arp_rep_unsolicited ≥ 5` (5초창) | ARP 스푸핑 (R1이 못 잡는 느린 경우 보강) |
| `mac_flood` | `feat_seg.new_src_macs ≥ 15` (1초창) | MAC 플러딩 |

- 임계치는 `detect.py` 상단 상수. 실험망 정상 호스트가 6대뿐이라 15를 기준으로 삼음.
- 같은 (공격자, 공격)은 10초에 한 번만 경보(data-format 2.4).
- 11주차에 가짜 DHCP·DHCP 고갈·포트 스캔·SYN flood 규칙 추가 예정.

## 검증 상태 (2026-11-13, 전체 파이프라인 실제 실행)

pcap → extract → detect → 라벨 대비 평가:

| 시나리오 | 탐지 | 경보 | 탐지시간 | 공격자 일치 | 정상구간 오탐 |
|---|---|---|---|---|---|
| arp_spoof | ✅ | 2건 | 1.56초 | ✅ (`…04`) | 0 |
| mac_flood | ✅ | 2건 | 1.3초 | — (아래 한계) | 0 |

→ **10주차 완료 기준 충족**: ARP 스푸핑 캡처를 넣으면 규칙 탐지기가 경보를 냄.

## 한계

- **MAC 플러딩 경보의 공격자 MAC이 null.** 오프라인 pcap에 입력 포트가 없고 출발지 MAC이
  매번 가짜라, 공격자를 특정할 수 없음. SDN 자동 차단(공격자 포트 차단)에는 **실시간 포트별
  캡처(12주차)**가 필요함. 탐지(경보 발생) 자체는 정상 동작.
