# dashboard/ — 대시보드와 알림 (P5)

실험 결과(경보)를 사람이 보기 좋게 보여주고, 디스코드로 알립니다.
데이터 로딩은 `load.py`(순수 함수, Streamlit 불필요)에 모여 있어 테스트가 쉽습니다.

## 구성

| 파일 | 내용 | 의존성 |
|---|---|---|
| `load.py` | 실험 폴더 → 요약·경보 표 | 표준 라이브러리만 |
| `app.py` | Streamlit 대시보드(경보 목록·탐지기별 집계·호스트) | streamlit |
| `notify.py` | 디스코드 웹훅 알림 (기본 미리보기) | 표준 라이브러리만 |

## 대시보드 실행

Streamlit은 시스템 numpy와 충돌해서 **전용 venv**에 설치합니다(탐지 파이프라인과 분리).

```bash
python3 -m venv ~/.venvs/dash
~/.venvs/dash/bin/pip install streamlit requests
~/.venvs/dash/bin/streamlit run dashboard/app.py
# 브라우저에서 http://localhost:8501
```

대시보드는 JSONL 파일만 읽으므로, 탐지 파이프라인(scapy/sklearn)이 도는 시스템 파이썬과
섞이지 않습니다.

## 디스코드 알림

```bash
# 미리보기(기본): 전송 없이 보낼 내용만 출력 — 외부로 아무것도 안 나감
python3 dashboard/notify.py data/runs/<run_id>

# 실제 전송: 각자 디스코드에서 웹훅 URL 발급 후
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python3 dashboard/notify.py data/runs/<run_id> --send
```

⚠️ 웹훅 URL은 비밀입니다. 저장소·채팅에 올리지 마세요.

## 검증 상태 (2026-11-13)

- ✅ `load.py` / `notify.format_alert`: `tests/test_dashboard.py`로 검증
- ✅ `notify.py` 미리보기: 실제 arp_spoof 경보를 디스코드 payload로 변환 확인(전송 안 함)
- ✅ `app.py`: 전용 venv에서 headless 실행 시 정상 기동(HTTP 200)

## 다음 단계 (12주차)

- 실시간 연결: 파일 꼬리를 읽어(`tail -f` 방식) 경보가 들어오면 바로 표시
- 트래픽 그래프, 탐지 근거(SHAP) 표시, 차단 해제 버튼
