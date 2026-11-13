# capture/ — 패킷 캡처와 특징 추출 (P2)

캡처(`capture.pcap`)에서 탐지기가 쓸 특징(`feat_host`, `feat_seg`)을 뽑습니다.
형식은 [`../docs/data-format.md`](../docs/data-format.md) 2.2, 2.3.

## 사용

```bash
# project/ 폴더에서 (WSL)
python3 capture/extract.py data/runs/<run_id>
# → features_1s.jsonl, features_5s.jsonl 생성
python3 common/records.py check data/runs/<run_id>
```

## 무엇을 계산하나

- **ARP 충돌(`arp_ip_conflicts`)**: 캡처를 시각 순서로 훑으며 IP-MAC 대응표를 **학습**하고
  (처음 본 쌍 등록, DHCP ACK로 갱신), 그 표와 다른 MAC이 같은 IP를 주장하면 충돌로 셈.
- **미요청 ARP 응답(`arp_rep_unsolicited`)**: 최근 5초 내 who-has 요청이 없던 ARP 응답.
- **구간별 새 MAC(`feat_seg.new_src_macs`)**: MAC 플러딩 신호.
- 그 외 패킷/바이트 수, DHCP·TCP·DNS 카운트 등(11주차 규칙용, 없으면 0).

## 검증 상태 (2026-11-13, 실제 pcap)

- ✅ arp_spoof/mac_flood 캡처에서 features 생성 → 형식 검사 통과
- ✅ ARP 스푸핑 캡처에서 공격자(`…04`)의 `arp_ip_conflicts=1` 정확히 계산
- ✅ MAC 플러딩 캡처에서 1초당 새 MAC 19~27개 계산

## 한계 (의도된 것)

- **오프라인 pcap은 '들어온 스위치 포트'를 담지 않음.** 미러 캡처에는 입력 포트 정보가 없어서,
  포트는 `meta.json`의 MAC→포트로 역산함. meta에 없는 MAC(플러딩용 가짜 MAC)은 포트 `null`
  구간으로 묶음(data-format 2.3의 null 허용). **포트별 정확 집계는 실시간 캡처(12주차)**에서.
- **대응표 학습은 "정상 통신이 먼저"임을 가정.** 시나리오의 워밍업 구간에서 진짜 IP-MAC이
  먼저 학습되므로 이후 사칭이 충돌로 잡힘. 워밍업 없이 공격이 가장 먼저 오면 오학습 가능.
