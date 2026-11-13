# 동작 확인 (CHECK)

환경 세팅 후, 자기 PC에서 전체 파이프라인이 도는지 **1회 확인**하는 절차입니다.
(공격 재현 → 캡처 → 특징 추출 → 규칙 탐지 → 성능 평가)

## 전제
- Windows + WSL2 Ubuntu, 공통 환경 세팅(README/공지 2번) 완료
- **clone 받은 `ComputerNetwork01` 폴더 안에서** 실행합니다. `project/` 폴더는 없습니다.

## 한 번에 실행
```bash
cd ComputerNetwork01
export PYTHONPATH=$PWD
sudo python3 env/run.py arp_spoof
D=$(ls -dt data/runs/*/ | head -1)
python3 capture/extract.py "$D"
python3 rules/detect.py "$D"
python3 eval/evaluate.py "$D"
```

## 단계별 + 성공 신호

| 단계 | 명령 | 성공 신호 |
|---|---|---|
| ① 실험 실행 (~45초, root) | `sudo python3 env/run.py arp_spoof` | `[run] … 완료`, `data/runs/<폴더>` 생성 |
| ② 폴더 찾기 | `D=$(ls -dt data/runs/*/ \| head -1)` | `echo $D`로 경로 확인 |
| ③ 특징 추출 | `python3 capture/extract.py "$D"` | `features_1s.jsonl 작성` |
| ④ 규칙 탐지 | `python3 rules/detect.py "$D"` | `경보 N개` (N ≥ 1) |
| ⑤ 성능 평가 | `python3 eval/evaluate.py "$D"` | 표에 `arp_spoof … 탐지 1/1 … 오탐 0` |

**성공 판단:** 마지막 표에 `arp_spoof 탐지 1/1, 오탐 0`이 보이면 세팅 완료.

## 형식 검사 (파일 공유 전)
```bash
python3 common/records.py check "$D"
```

## 자주 겪는 오류

| 증상 | 원인 / 해결 |
|---|---|
| `mn: command not found` | 패키지 미설치 → 공지 2번 apt 설치 다시 |
| `permission denied`, `RTNETLINK` | `sudo` 빠짐 → `sudo python3 env/run.py …` |
| `ModuleNotFoundError: common` | `export PYTHONPATH=$PWD` 안 했거나 폴더 위치 틀림 |
| `capture.pcap 없음` | `--no-pcap`로 돌렸거나 OVS 미러 실패 → `env/run.py arp_spoof` 다시 |
| streamlit 관련 오류 | 대시보드(P5)만 필요. `~/.venvs/dash` venv에서 실행 |

안 되면 터미널 화면을 캡처해 단톡방에 공유해 주세요.
