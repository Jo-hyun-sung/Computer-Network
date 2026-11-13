# model/ — AI 모델 (P3)

규칙과 **같은 특징**(`feat_host`)을 입력받아 공격을 판정하고, **같은 경보 형식**
(`alerts_ai.jsonl`, data-format 2.4)을 출력합니다. 그래서 `eval/`로 규칙 vs AI를
바로 비교할 수 있습니다.

## 사용

```bash
# 학습 (data/runs 전체 또는 특정 실험)
python3 model/train.py --all
# 추론 → alerts_ai.jsonl
python3 model/infer.py data/runs/<run_id> --threshold 0.5
# 비교
python3 eval/evaluate.py data/runs/<run_id>
```

산출물 `model/rf.joblib`, `model/metrics.json`은 재생성되므로 저장소에 올리지 않습니다
(`.gitignore`). 데이터로부터 위 명령으로 다시 만듭니다.

## 구성

| 파일 | 내용 |
|---|---|
| `dataset.py` | 실험 폴더들의 `feat_host`에 라벨을 붙여 (X, y) 생성 |
| `train.py` | 랜덤포레스트 학습·평가(혼동행렬·특징중요도)·저장 |
| `infer.py` | 학습된 모델로 경보 생성 |

## 라벨링

`feat_host` 기록의 시각이 공격 구간 안이고 그 기록의 `host.mac`이 공격자 MAC과 같으면
그 공격, 아니면 `normal`. **MAC 플러딩·DHCP 고갈은 가짜 MAC을 쓰므로 호스트 단위로는
공격자가 드러나지 않습니다** → 이 모델의 사각지대. 플러딩류는 규칙(`feat_seg`)이 담당하고,
구간 단위 모델은 이후 과제로 둡니다.

## 기준 모델 결과 (2026-11-13, 실험망 데이터, Kitsune 미사용)

- 표본 약 3,400개(정상 3,287 / arp_spoof 155) — 공격 1종 + 정상
- 학습에서 **뺀** 실험으로 평가:

| 공격 | 규칙 | AI |
|---|---|---|
| arp_spoof | 탐지 1/1, 오탐 0, 1.17초 | 탐지 1/1, 오탐 0, 1.17초 |
| mac_flood | 탐지 1/1 | **못 잡음**(호스트 모델 사각지대) |

- 특징 중요도: `arp_ip_conflicts`(0.36) > `arp_rep`(0.19) > `arp_ip_claims`(0.17) …
  → **AI가 규칙과 사실상 같은 신호를 학습**함. "일반 공격은 규칙으로 충분, AI의 가치는
  회피 공격에서"라는 프로젝트 논점과 일치. (회피 공격 비교는 13주차)

## 한계 / 다음 단계

- **Kitsune 미사용**: 지금은 실험망 데이터만. 11주차에 Kitsune 데이터셋 전처리·추가 학습.
- **공격 1종**: arp_spoof만 양성. 11주차에 가짜DHCP·스캔·SYN flood를 추가하면 다중 분류.
- **평가 낙관 가능성**: 같은 토폴로지에서 생성한 데이터라 실제보다 쉬움. 공격별 교차검증 권장.
- **플러딩 사각지대**: `feat_seg` 기반 모델 추가 검토.
