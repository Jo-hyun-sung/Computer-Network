"""랜덤포레스트 기준 모델 학습·평가·저장 (P3).

    python3 model/train.py --all                 # data/runs 전체로 학습
    python3 model/train.py data/runs/<run_id> ...

출력:
  model/rf.joblib      학습된 모델 + 특징 이름 + 클래스
  model/metrics.json   평가 지표(정확도, 클래스별 precision/recall, 혼동행렬)

기준 모델이므로 목표는 "규칙과 비교할 출발점"입니다. 특징 중요도를 함께 출력해
어떤 특징이 판정을 주도하는지(예: arp_ip_conflicts) 확인합니다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.dataset import FEATURES, all_runs, build  # noqa: E402


def main() -> None:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split
    import joblib

    p = argparse.ArgumentParser(description="RF 기준 모델 학습 (P3)")
    p.add_argument("run_dirs", nargs="*")
    p.add_argument("--all", action="store_true", help="data/runs 전체")
    p.add_argument("--test-size", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()

    runs = list(a.run_dirs) + (all_runs() if a.all else [])
    if not runs:
        sys.exit("학습할 실험 폴더가 없습니다. --all 또는 폴더를 지정하세요.")
    X, y, meta = build(runs)
    if not X:
        sys.exit("feat_host 기록이 없습니다. 먼저 capture/extract.py 실행.")

    X = np.array(X, dtype=float)
    y = np.array(y)
    classes, counts = np.unique(y, return_counts=True)
    print(f"[train] 표본 {len(y)}개, 클래스 분포:",
          {c: int(n) for c, n in zip(classes, counts)})
    if len(classes) < 2:
        sys.exit(f"클래스가 1개뿐({classes[0]})이라 학습 불가. 공격·정상 데이터가 모두 필요.")

    # 각 클래스 표본이 2개 이상이면 층화 분할, 아니면 전체로 학습 후 train 평가
    stratify = y if min(counts) >= 2 else None
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=a.test_size, random_state=a.seed, stratify=stratify)

    clf = RandomForestClassifier(n_estimators=200, random_state=a.seed,
                                 class_weight="balanced", n_jobs=-1)
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)

    labels_sorted = sorted(classes.tolist())
    print("\n[평가] 테스트셋 분류 리포트")
    print(classification_report(yte, pred, labels=labels_sorted, zero_division=0))
    cm = confusion_matrix(yte, pred, labels=labels_sorted)
    print("혼동행렬 (행=정답, 열=예측):", labels_sorted)
    for name, row in zip(labels_sorted, cm):
        print(f"  {name:12s} {row.tolist()}")

    imp = sorted(zip(FEATURES, clf.feature_importances_),
                 key=lambda t: -t[1])[:8]
    print("\n[특징 중요도] 상위 8")
    for name, v in imp:
        print(f"  {name:22s} {v:.3f}")

    rep = classification_report(yte, pred, labels=labels_sorted,
                                zero_division=0, output_dict=True)
    metrics = {
        "samples": len(y), "classes": {c: int(n) for c, n in zip(classes, counts)},
        "test_size": a.test_size, "report": rep,
        "confusion_matrix": {"labels": labels_sorted, "matrix": cm.tolist()},
        "feature_importance": {k: float(v) for k, v in
                               zip(FEATURES, clf.feature_importances_)},
    }
    (ROOT / "model" / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    joblib.dump({"model": clf, "features": FEATURES,
                 "classes": clf.classes_.tolist()}, ROOT / "model" / "rf.joblib")
    print("\n[저장] model/rf.joblib, model/metrics.json")


if __name__ == "__main__":
    main()
