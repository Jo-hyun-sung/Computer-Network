# 강의 실습 표준 환경
# 목적은 성능이 아니라 재현성 - 전원이 같은 버전, 같은 출력
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      tshark tcpdump \
      dnsutils curl ca-certificates \
      iproute2 iputils-ping traceroute mtr-tiny \
      iperf3 ipcalc \
      python3 python3-pip jq less vim-tiny \
 && rm -rf /var/lib/apt/lists/*

# tshark 를 비루트로 쓰기 위한 설정 - 컨테이너 안 캡처용
# 실제 캡처는 호스트 Wireshark 로 하므로 분석에만 씁니다
RUN groupadd -f wireshark && usermod -aG wireshark root

WORKDIR /practice
CMD ["/bin/bash"]
