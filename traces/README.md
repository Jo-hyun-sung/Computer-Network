# 공식 trace 파일

교재 저자가 제공하는 캡처 파일입니다. 직접 캡처가 막힐 때 쓰는 **경로 (B)** 입니다.

## 받는 곳

<https://gaia.cs.umass.edu/kurose_ross/wireshark.php>

**9판(9.0) 버전**을 받으세요. 8.1 · 8.0 은 절 번호와 내용이 다릅니다.

## 이 과목에서 쓰는 것

| 주차 | 랩 이름 | 쓰는 곳 |
|---|---|---|
| 3 | DNS | 계층 조회 · 레코드 종류 |
| 4 | TCP (+ UDP) | handshake · 순서 번호 · 재전송 |
| 5 | IP · NAT · DHCP | 주소 · 변환 · DORA |
| 7 | Ethernet and ARP | 요청 · 응답 · 브로드캐스트 주소 |

6주차(제어 평면)는 대응하는 공식 랩이 없어 자체 설계입니다.
**9판에는 ICMP 랩이 없습니다**(8.0 판만 존재).

## 출처 표기

저자 이용 조건입니다. 보고서에 trace 를 쓰면 아래를 넣으세요.

> Wireshark lab trace files from J.F. Kurose and K.W. Ross,
> *Computer Networking: A Top-Down Approach*, 9th ed.
> <https://gaia.cs.umass.edu/kurose_ross/>
> Copyright 1996-2025 J.F. Kurose, K.W. Ross. All Rights Reserved.

## 저장소에 포함하지 않는 이유

용량이 크고 저자 사이트가 원본입니다. 각자 받아서 이 폴더에 두세요.
이 폴더의 `.pcapng` 는 `.gitignore` 로 커밋되지 않습니다.
