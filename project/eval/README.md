# eval/ — 비교 실험과 성능 평가 (P5)

실험 폴더의 `labels / alerts / actions / features`를 읽어
[`../docs/data-format.md`](../docs/data-format.md) 4장 정의대로 성능표를 자동 계산합니다.

## 사용

```bash
python3 eval/evaluate.py data/runs/<run_id> [...]       # 특정 실험
python3 eval/evaluate.py --all                           # data/runs 전체
python3 eval/evaluate.py --all --out eval/results/summary.md
```

여러 탐지기의 경보 파일을 모두 읽어 `detector`별(규칙/AI/혼합)로 나눠 집계합니다
(`alerts.jsonl`, `alerts_rule.jsonl`, `alerts_ai.jsonl` 중 있는 것).

## 지표 (data-format 4장)

| 열 | 뜻 |
|---|---|
| 탐지 | 경보가 1개 이상 난 공격 수 / 전체 공격 수 |
| TP / FP | 맞은 경보 / 틀린 경보 |
| 탐지시간 | 첫 TP 경보 시각 − 공격 시작 시각 (평균) |
| 대응시간 | 첫 block action 시각 − 공격 시작 시각 (SDN 연결 후, 12주차) |
| 공격자특정 | 경보의 `attacker.mac`이 정답과 일치(O) / 불일치(X) / 미지정(-) |
| 정상구간오탐 | 공격 밖(정상)에서 난 경보 수 |

판정 기준(팀 공통): `attack`이 같고 `ts`가 `[start, end + 5초]` 안이면 TP.
`attack`은 맞아도 `attacker.mac`이 정답과 다르면 **FP**(엉뚱한 PC를 차단하게 되므로).
`attacker.mac`이 `null`이면 '미지정'으로 보고 FP로 세지 않음(오프라인 MAC 플러딩 등).

## 현재 결과 (2026-11-13, 규칙 탐지기)

| 공격 | 탐지 | TP | FP | 탐지시간 | 공격자특정 | 정상구간오탐 |
|---|---|---|---|---|---|---|
| arp_spoof | 1/1 | 2 | 0 | 1.56초 | O (`…04`) | 0 |
| mac_flood | 1/1 | 2 | 0 | 1.30초 | X (오프라인 한계) | 0 |

지표 계산 로직은 `../tests/test_evaluate.py`(7개)로 검증됨: 공격자 오지정·정상구간
경보가 실제로 FP로 집계되고, GRACE 경계·대응시간·탐지율이 정의대로 나옴.
`results/`에는 생성된 요약표가 들어갑니다(용량이 작아 올려도 됨).
