"""학습된 모델로 경보 생성 (P3 추론).

실험 폴더의 feat_host 기록을 모델에 넣어, 공격으로 예측되면 alerts_ai.jsonl 을
만듭니다. 형식은 규칙 탐지기와 동일(data-format 2.4)이라 eval로 규칙 vs AI 비교 가능.

    python3 model/infer.py data/runs/<run_id>
    python3 model/infer.py data/runs/<run_id> --threshold 0.5

같은 (공격자, 공격)은 10초에 한 번만 경보(규칙과 동일 기준).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import make, read, write  # noqa: E402

DEDUP_SEC = 10.0


def infer(run_dir: Path, threshold: float, model_path: Path) -> None:
    import numpy as np
    import joblib

    bundle = joblib.load(model_path)
    clf, feats, classes = bundle["model"], bundle["features"], bundle["classes"]

    recs = []
    for w in (1, 5):
        f = run_dir / f"features_{w}s.jsonl"
        if f.exists():
            recs += [r for r in read(f) if r.get("type") == "feat_host"]
    recs.sort(key=lambda r: r["ts"])
    if not recs:
        sys.exit(f"feat_host 기록 없음: {run_dir}")

    X = np.array([[float(r.get(k, 0) or 0) for k in feats] for r in recs], dtype=float)
    proba = clf.predict_proba(X)
    cls_idx = {c: i for i, c in enumerate(classes)}

    last: dict[tuple, float] = {}
    n = 0
    seq = 0
    out = run_dir / "alerts_ai.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for i, (r, pr) in enumerate(zip(recs, proba)):
            # normal을 제외한 최고 확률 공격
            best, best_p = None, 0.0
            for c, ci in cls_idx.items():
                if c != "normal" and pr[ci] > best_p:
                    best, best_p = c, pr[ci]
            if best is None or best_p < threshold:
                continue
            host = r["host"]
            key = (best, host["mac"])
            if host["mac"] and last.get(key, -1e9) > r["ts"] - DEDUP_SEC:
                continue
            last[key] = r["ts"]
            seq += 1
            top = sorted(((feats[j], float(X[i][j])) for j in range(len(feats))),
                         key=lambda t: -t[1])[:4]
            write(fh, make("alert", ts=r["ts"], alert_id=f"ai-{seq:06d}",
                           detector="ai", source="rf-v1", attack=best,
                           score=round(float(best_p), 4), attacker=host, victim=None,
                           feature_ts=r["ts"], win=r["win"],
                           summary=f"AI: {host['mac']}의 트래픽이 {best}와 유사 ({best_p:.0%})",
                           evidence={"proba": round(float(best_p), 4),
                                     "top_features": top}))
            n += 1
    print(f"[infer] {out.name}: 경보 {n}개 (임계치 {threshold})")


def main() -> None:
    p = argparse.ArgumentParser(description="AI 추론 → 경보 (P3)")
    p.add_argument("run_dir")
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--model", default=str(ROOT / "model" / "rf.joblib"))
    a = p.parse_args()
    infer(Path(a.run_dir), a.threshold, Path(a.model))


if __name__ == "__main__":
    main()
