# 모듈 간 데이터 형식 (v1)

모든 모듈(env, capture, model, rules, sdn, dashboard, eval)은 이 문서의 형식으로만 데이터를 주고받습니다.
형식을 바꾸려면 이 문서를 먼저 고치고 팀에 알린 뒤 `v` 값을 올립니다.

검사 도구: `python common/records.py check <파일.jsonl 또는 폴더>` (통과 0, 형식 오류 1, 경로 오류 2를 돌려줌)
도구 자체 테스트: `python -m unittest discover -s tests` (Python 3.8 이상)
예시: [`docs/examples/run-sample/`](examples/run-sample/)

---

## 1. 공통 규칙

| 항목 | 규칙 |
|---|---|
| 파일 형식 | **JSON Lines** (`.jsonl`): 한 줄에 기록 하나, UTF-8 |
| 시각 `ts` | **Unix epoch 초, 실수** (`time.time()` 값, 예: `1763020800.123`). 모든 모듈이 같은 기준을 씀 |
| 시각 출처 | 실시간: 기록을 만든 순간의 `time.time()`. 캡처 파일 재생: 패킷의 캡처 시각 |
| 공통 필드 | 모든 기록에 `v`(형식 버전, 지금은 `1`), `type`(기록 종류), `ts`를 넣음 |
| MAC | 소문자, 콜론 구분 (`00:00:00:00:00:04`) |
| IP | 문자열 (`10.0.0.4`) |
| 모르는 값 | 필드를 빼지 말고 `null` |
| 추가 값 | 형식에 없는 값은 `extra` 객체 안에 넣음 (다른 모듈은 무시해도 됨). **바깥에 두면 검사에서 오류**가 남. 오타(`arp_reps`)가 조용히 0으로 바뀌는 사고를 막기 위함 |
| 시각 필드 | 이름이 `_ts`로 끝나는 필드(`start_ts`, `feature_ts`, `expires_ts`)도 `ts`와 같은 규칙. 밀리초를 넣으면 오류 |
| 인코딩 | UTF-8. BOM이 붙은 파일(PowerShell `Out-File`)도 읽을 수 있음 |

> Mininet의 모든 호스트는 같은 커널 시계를 공유하므로, 모듈끼리 시각이 어긋나지 않습니다.
> 대응 시간(공격 시작 → 탐지 → 차단)을 기록의 `ts` 차이로 바로 계산할 수 있습니다.

### 공격 종류 `attack`

| 값 | 공격 | 주차 |
|---|---|---|
| `normal` | 정상 | |
| `arp_spoof` | ARP 스푸핑 / 중간자 공격 | w07 |
| `mac_flood` | MAC 플러딩 (CAM 테이블 고갈) | w07 |
| `dhcp_rogue` | 가짜 DHCP 서버 | w05 |
| `dhcp_starve` | DHCP 고갈 | w05 |
| `port_scan` | 네트워크·포트 스캔 | w04 |
| `syn_flood` | SYN flood | w04 |
| `dns_spoof` | DNS 스푸핑 (확장 목표) | w03 |

### 공격자·대상 표기 `endpoint`

```json
{"mac": "00:00:00:00:00:04", "ip": "10.0.0.4", "sw": "s1", "port": 4}
```

`sw`는 스위치 이름(Mininet `s1`)이고 `port`는 그 스위치의 포트 번호(`s1-eth4`이면 `4`)입니다. 모르면 `null`로 둡니다.
SDN 차단은 이 네 값만 보고 규칙을 설치합니다.

---

## 2. 기록 종류

```
 P1 env ──label──────────────────────────────────────────┐
                                                         ▼
 P2 capture ──feat_host / feat_seg──▶ P3 model ──alert──▶ P5 eval / dashboard
                                  └─▶ P4 rules ──alert──┤
                                                        ▼
                                       P4 sdn ──action──▶ P5 eval / dashboard
```

| `type` | 만드는 쪽 | 쓰는 쪽 | 파일 |
|---|---|---|---|
| `label` | P1 env | P3(학습), P5(평가) | `labels.jsonl` |
| `feat_host` | P2 capture | P3, P4 | `features_1s.jsonl`, `features_5s.jsonl` |
| `feat_seg` | P2 capture | P3, P4 | (같은 파일에 섞어서 저장) |
| `alert` | P3 model, P4 rules | P4 sdn, P5 | `alerts.jsonl` |
| `action` | P4 sdn | P5 | `actions.jsonl` |

### 2.1 `label`: 정답 (P1)

공격 스크립트가 **시작할 때와 끝날 때** 기록합니다. 기록이 없는 시간은 모두 `normal`입니다.

| 필드 | 형식 | 설명 |
|---|---|---|
| `ts` | 실수 | 기록한 시각 (= `end_ts`) |
| `attack_id` | 문자열 | 실험 안에서 유일 (`a01`, `a02`, ...) |
| `attack` | 공격 종류 | `normal` 제외 |
| `start_ts` | 실수 | 공격 첫 패킷을 보낸 시각 |
| `end_ts` | 실수 | 공격 마지막 패킷을 보낸 시각 |
| `attacker` | endpoint | 공격자 |
| `target` | endpoint 또는 `null` | 피해자 (스캔, 플러딩처럼 대상이 여럿이면 `null`) |
| `evasive` | 참/거짓 | 회피 공격(느린 스푸핑, 느린 스캔, 정상 트래픽에 섞기)이면 `true` |
| `params` | 객체 | 도구, 속도 등 (`{"tool": "arpspoof", "rate_pps": 1}`) |

### 2.2 `feat_host`: 호스트별 특징 (P2)

**창(window) 하나 × 출발지 MAC 하나**마다 한 줄입니다. 창 크기는 1초와 5초 두 가지이고, 창이 끝나는 시각에 만듭니다.
그 창에서 패킷을 하나도 보내지 않은 MAC은 기록하지 않습니다.

| 필드 | 형식 | 설명 |
|---|---|---|
| `ts` | 실수 | 창이 끝난 시각 |
| `win` | 정수 | 창 크기(초): `1` 또는 `5` |
| `host` | endpoint | 출발지 MAC, 그 MAC이 가장 많이 쓴 IP, 들어온 스위치 포트 |
| `pkts`, `bytes` | 정수 | 보낸 패킷 수, 바이트 수 |
| `arp_req` | 정수 | 보낸 ARP 요청 |
| `arp_rep` | 정수 | 보낸 ARP 응답 |
| `arp_grat` | 정수 | 보낸 Gratuitous ARP (보낸 IP = 찾는 IP) |
| `arp_rep_unsolicited` | 정수 | 최근 5초 안에 요청이 없었는데 보낸 응답 |
| `arp_ip_claims` | 정수 | ARP로 "내 IP"라고 주장한 서로 다른 IP 수 |
| `arp_ip_conflicts` | 정수 | 주장한 IP 중, 대응표에 **다른 MAC**으로 등록된 IP 수 |
| `dhcp_offer`, `dhcp_ack` | 정수 | 보낸 DHCP OFFER, ACK (서버 역할) |
| `dhcp_discover` | 정수 | 보낸 DHCP DISCOVER |
| `tcp_syn` | 정수 | 보낸 SYN (ACK 없는 SYN) |
| `tcp_synack_in` | 정수 | 받은 SYN+ACK |
| `tcp_rst_in` | 정수 | 받은 RST |
| `icmp_unreach_in` | 정수 | 받은 ICMP 도달 불가 |
| `dst_ips` | 정수 | 보낸 패킷의 서로 다른 목적지 IP 수 |
| `dst_ports` | 정수 | 보낸 TCP/UDP의 서로 다른 목적지 포트 수 |
| `top_dst_share` | 실수 0~1 | 가장 많이 보낸 목적지 IP의 패킷 비율 |
| `dns_resp` | 정수 | 보낸 DNS 응답 (DNS 스푸핑용) |
| `extra` | 객체 | 모델 전용 특징 (예: Kitsune AfterImage 값) |

**IP-MAC 대응표:** `arp_ip_conflicts`는 P2가 실험 동안 유지하는 대응표를 기준으로 셉니다.
처음 본 (IP, MAC) 쌍을 등록하고, DHCP ACK를 보면 그 값으로 갱신합니다.
사전 차단(P4)도 같은 원리로 동작하므로, 대응표 규칙은 P2와 P4가 같이 정합니다.

### 2.3 `feat_seg`: 구간별 특징 (P2)

**창 하나 × 스위치 포트 하나**마다 한 줄입니다. MAC 플러딩과 DHCP 고갈은 가짜 MAC을 많이 만들어 쓰기 때문에, MAC별로 세면 공격이 1~2개씩 흩어집니다. 그래서 포트별로 따로 셉니다.
포트를 알 수 없는 캡처(예: 공개 데이터셋)는 `sw`, `port`를 `null`로 두고 LAN 전체를 한 구간으로 봅니다.

| 필드 | 형식 | 설명 |
|---|---|---|
| `ts`, `win` | | `feat_host`와 같음 |
| `sw`, `port` | 문자열, 정수 | 구간 (패킷이 들어온 스위치 포트) |
| `pkts`, `bytes` | 정수 | 이 포트로 들어온 패킷 수, 바이트 수 |
| `src_macs` | 정수 | 서로 다른 출발지 MAC 수 |
| `new_src_macs` | 정수 | 이번 실험에서 처음 본 출발지 MAC 수 |
| `dhcp_discover` | 정수 | DHCP DISCOVER 수 |
| `dhcp_chaddrs` | 정수 | DISCOVER/REQUEST 안의 서로 다른 클라이언트 MAC(chaddr) 수 |
| `dhcp_offer` | 정수 | DHCP OFFER 수 |
| `dhcp_servers` | 정수 | OFFER를 보낸 서로 다른 MAC 수 |
| `arp_rep` | 정수 | ARP 응답 수 |
| `tcp_syn` | 정수 | SYN 수 |
| `extra` | 객체 | 추가 특징 |

### 2.4 `alert`: 경보 (P3, P4)

탐지기가 공격이라고 판단하면 한 줄을 씁니다. **같은 공격자의 같은 공격은 10초에 한 번만** 경보를 냅니다(경보 폭주 방지). 묶는 시간은 설정으로 바꿀 수 있게 합니다.

| 필드 | 형식 | 설명 |
|---|---|---|
| `ts` | 실수 | 판정을 마친 시각 |
| `alert_id` | 문자열 | 유일 (`rule-000123`, `ai-000045`) |
| `detector` | `rule` / `ai` / `hybrid` | 탐지 방식 |
| `source` | 문자열 | 규칙 이름 또는 모델 이름 (`arp_conflict`, `rf-v2`) |
| `attack` | 공격 종류 | 판정한 공격 |
| `score` | 실수 0~1 | 확신 정도 (규칙은 `1.0`) |
| `attacker` | endpoint | 차단할 대상 |
| `victim` | endpoint 또는 `null` | 피해자 |
| `feature_ts` | 실수 | 근거가 된 특징 기록의 `ts` |
| `win` | 정수 | 근거가 된 창 크기 |
| `summary` | 문자열 | 대시보드에 보일 한 줄 설명 (한국어) |
| `evidence` | 객체 | 판단 근거 값 (규칙: 넘은 임계치, AI: 상위 SHAP 특징) |

### 2.5 `action`: 차단·해제 (P4 sdn)

| 필드 | 형식 | 설명 |
|---|---|---|
| `ts` | 실수 | 스위치에 규칙 설치가 **끝난** 시각 |
| `action` | `block` / `unblock` / `pre_drop` | 사후 차단 / 해제 / 사전 차단(대응표와 안 맞는 ARP 버림) |
| `target` | endpoint | 차단 대상 |
| `alert_id` | 문자열 또는 `null` | 원인 경보 (사전 차단, 수동 해제는 `null`) |
| `reason` | 문자열 | 사유 |
| `expires_ts` | 실수 또는 `null` | 자동 해제 시각 (`null`이면 영구) |
| `ok` | 참/거짓 | 설치 성공 여부 |
| `install_ms` | 실수 | 명령을 보낸 뒤 설치가 끝날 때까지 걸린 시간 |

---

## 3. 실험 1회분 폴더 구조

실험 1회(= 시나리오 1번 실행)마다 폴더를 하나 만듭니다.

```
data/runs/<run_id>/            run_id = YYYYMMDD-HHMMSS-<시나리오>  예: 20261117-143000-arp_spoof
├── meta.json                  실험 정보 (아래)
├── capture.pcap               원본 캡처 (공개 전 익명화)
├── labels.jsonl               P1
├── features_1s.jsonl          P2 (feat_host, feat_seg)
├── features_5s.jsonl          P2
├── alerts.jsonl               P3, P4 (탐지기마다 따로 쓰면 alerts_rule.jsonl, alerts_ai.jsonl)
└── actions.jsonl              P4
```

`data/`는 용량이 크므로 저장소에 올리지 않습니다(`.gitignore`). 공유할 실험만 익명화해서 따로 올립니다.

### `meta.json`

```json
{
  "v": 1,
  "run_id": "20261117-143000-arp_spoof",
  "scenario": "arp_spoof",
  "start_ts": 1763357400.0,
  "end_ts": 1763357520.0,
  "topology": "single switch s1, 5 hosts",
  "hosts": [
    {"name": "h1", "role": "client",  "mac": "00:00:00:00:00:01", "ip": "10.0.0.1", "sw": "s1", "port": 1},
    {"name": "gw", "role": "gateway", "mac": "00:00:00:00:00:fe", "ip": "10.0.0.254", "sw": "s1", "port": 5},
    {"name": "h4", "role": "attacker","mac": "00:00:00:00:00:04", "ip": "10.0.0.4", "sw": "s1", "port": 4}
  ],
  "dhcp_servers": ["00:00:00:00:00:fd"],
  "notes": ""
}
```

`hosts`의 `role`이 `attacker`인 호스트가 정답 공격자입니다. `dhcp_servers`는 정상 DHCP 서버 목록이며, 가짜 DHCP 판정과 사전 차단에 씁니다.

---

## 4. 평가 기준 (P5)

평가 스크립트는 아래 정의로 계산합니다. 숫자가 팀원마다 달라지지 않도록 미리 정해 둡니다.

| 지표 | 정의 |
|---|---|
| 맞은 경보 (TP) | `attack`이 같고, `ts`가 `[start_ts, end_ts + 5초]` 안에 있는 label이 있는 경보 |
| 틀린 경보 (FP) | 위 조건을 만족하는 label이 없는 경보 |
| 탐지율 | 경보가 1개 이상 나온 공격 수 ÷ 전체 공격 수 (label 기준) |
| 오탐률 | 정상 구간 1시간당 FP 개수, 그리고 정상 창 중 경보가 난 창의 비율 |
| 탐지 시간 | 첫 TP 경보의 `ts` − `start_ts` |
| 대응 시간 | 그 경보로 생긴 첫 `block` action의 `ts` − `start_ts` |

공격자를 잘못 짚은 경보(`attack`은 맞지만 `attacker.mac`이 다름)는 **틀린 경보로 셉니다**. 잘못 짚으면 엉뚱한 PC를 차단하기 때문입니다.

---

## 5. 실시간 전달 (12주차)

실시간으로 연결할 때도 **같은 JSON 한 줄 형식**을 그대로 씁니다. 바뀌는 것은 전달 방법뿐입니다.

- 기본 방법: 만드는 쪽이 파일 끝에 한 줄씩 추가하고(`flush`), 받는 쪽이 파일 끝을 계속 읽음 (`tail -f` 방식)
- 지연이 문제가 되면 12주차에 로컬 소켓으로 바꿉니다. 형식은 그대로 유지합니다.

---

## 6. 개인정보

- 실험은 Mininet 가상 MAC(`00:00:00:00:00:0X`)만 씁니다.
- 실제 PC에서 캡처한 파일은 올리기 전에 MAC과 IP를 익명화합니다. 기록 파일과 pcap은 같은 대응표로 바꿉니다.

## 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v1 | 2026-11-13 | 최초 작성 |
| v1 | 2026-11-13 | 검사 강화: 모르는 필드 거부, `_ts` 필드 시각 검사, MAC 형식 엄격화, BOM 허용 (형식 자체는 그대로) |
