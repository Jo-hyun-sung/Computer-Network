# Task 1 · 반복형 리졸버

루트 서버는 `www.korea.ac.kr`의 주소를 아예 갖고 있지 않다. 자기 밑의 TLD(`.kr`, `.com`...)가 누군지만 알고, 나머지는 위임한다. 모든 도메인을 루트에 다 넣으면 계층 구조를 만든 의미가 없어진다.

glue 없는 위임을 만났을 때(`www.stanford.edu`, 총 27홉)는 그 네임서버 이름을 루트부터 다시 resolve했다. "recursive resolver"라는 이름의 재귀가 여기서 나오는 것 같다 — glue 없는 NS 하나당 root→TLD→auth 왕복이 통째로 하나 더 붙는다.

대부분 3~6개 서버만 물어보면 끝났다. 내 노트북의 리졸버는 이 과정을 자기가 설정된 리졸버한테 **딱 한 번** 물어보는 걸로 퉁친다 — stub resolver의 편리함이 바로 이거다.

# Task 2 · DNS가 진짜로 유도하나?

**규칙**: CNAME 체인의 끝이 원래 사이트와 다른 등록 도메인이고, 같은 조직 것도 아니면 third-party로 판단.

**틀린 사례**: `www.wikipedia.org` → `wikimedia.org`. 도메인만 비교하면 third-party로 오판하지만, 사실은 같은 조직이 다른 도메인으로 자체 인프라 운영하는 것(netflix.com이 자기 CDN 쓰는 거랑 같은 패턴). CNAME만 보고는 "자체 운영 vs 외주"를 구분 못 한다. 반대로 `www.korea.ac.kr`은 CNAME이 아예 없어서, anycast CDN 뒤에 숨어있어도 이 규칙은 절대 못 잡아낸다.

**Steering number**:
- 리졸버 기준(한 네트워크): CDN 사이트 8개 중 **7개**가 리졸버 바꾸면 다른 주소를 줌
- 네트워크 기준(집/랩 Wi-Fi → 폰 테더링, B3): 8개 중 **3개**(Microsoft, Adobe, Apple — 전부 Akamai)만 네트워크 바뀌면 답도 바뀜. Fastly/Netlify 쓰는 나머지 5개는 완전히 똑같은 답. 이건 Akamai는 DNS 답 자체를 클라이언트 위치별로 바꿔주는 방식이고, Fastly/Netlify는 anycast라서(같은 IP를 여러 곳에서 뿌리고 라우팅이 알아서 가까운 곳으로 보냄) DNS가 바뀔 필요가 없기 때문. 그래서 "DNS가 유도하는가"는 CDN 벤더에 따라 답이 다르다.

**Part A (캡처)**: delegation과 answer는 사실 완전히 같은 DNS 메시지 포맷이고, 어느 섹션이 채워졌냐만 다르다. 루트 서버 응답(frame 2)은 answer 0개, authority에 NS 6개 — "모른다, 대신 여기 물어봐". 권한 서버 응답(frame 42)은 answer에 A 레코드 1개, authority/additional은 비어있음 — "내가 갖고 있다". 헤더 플래그로는 구분 안 되고 섹션 내용으로만 구분된다.

**참고**: 컨테이너 안에서 `test_tasks.py`를 돌리면 캡처 체크가 "0 queries, 0 responses"로 실패로 뜨는데, 이건 캡처가 비어서가 아니라 harness가 `dns.flags.response`를 문자열 `"0"`/`"1"`로 비교하는데 컨테이너의 tshark 4.2.2는 이 값을 `True`/`False`로 출력해서 생기는 버전 문제다. 직접 `tshark -r out/dns.pcapng -Y dns -T fields -e dns.flags.response`로 확인하면 query 22개, response 22개 다 들어있다.

# Task 3 · 캐시 개선

`BaselineCache`의 문제 두 개, 원인은 같음(TTL을 아예 안 봄):
- **정확성 버그**: 무조건 60초 고정으로 캐싱. TTL 20초짜리(`www.microsoft.com`)는 만료 후에도 최대 60초까지 그대로 내보내서 stale 266건이 여기서 나옴.
- **성능 버그**: `self.entries`가 리스트라 조회할 때마다 선형 탐색.

`YourCache`는 `(주소, 만료시각)`을 dict에 저장해두고 만료됐을 때만 upstream에 물어봄 → upstream 275회, stale 0.

**Floor**: 275가 이 워크로드에서 나올 수 있는 최소값. prefetch 없이 요청 들어올 때만 캐싱하는 방식이면, 이름당 최초 1회 + 이후 TTL 만료 후 재요청 올 때마다 1회씩은 upstream에 가야 한다. `YourCache`는 딱 그 경계(`now >= 만료시각`)에서만 다시 가져오므로 더 줄일 방법이 없다(미래를 예측하지 않는 이상).

가장 타격이 큰 레코드는 `www.microsoft.com` — TTL이 제일 짧은데(20초) 동시에 제일 자주 조회되는 이름이라, 고정-60초 정책이 여기서 stale을 제일 많이 만든다.
