# 프로젝트 주제 제출

- **팀 이름:** TBD
- **팀원:** TBD (팀장), TBD, TBD, TBD, TBD
- **프로젝트 제목:** AI 기반 LAN 공격 탐지 및 자동 대응 시스템
- **GitHub 저장소:** https://github.com/Jo-hyun-sung/Computer-Network/tree/main/project

## 설명

ARP와 DHCP는 인증 절차가 없어서, 같은 LAN 안의 공격자가 ARP 스푸핑이나 가짜 DHCP 서버만으로 중간자 공격을 할 수 있지만 일반 사용자는 이를 알아채기 어렵다. 본 프로젝트는 격리된 가상 LAN(Mininet)에서 이러한 공격을 재현하고, Scapy로 실시간 캡처한 패킷에서 ARP, DHCP, 플로우 특징을 추출한다. 공개 데이터셋(Kitsune Network Attack)과 직접 수집한 트래픽으로 학습한 AI 모델과 규칙 기반 탐지기로 공격을 판정하고, 두 방식의 탐지율, 오탐률, 탐지 시간을 비교한다. 최종 결과물은 공격 종류와 판단 근거를 실시간으로 보여주는 경보 대시보드와, 공격자 포트를 자동으로 차단하는 SDN 컨트롤러이다.
