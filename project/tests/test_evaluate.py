"""eval/evaluate.py 지표 계산 검증 (Mininet 불필요, 표준 라이브러리만)."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval"))

from common.records import endpoint, make, write  # noqa: E402
import evaluate  # noqa: E402

T = 1763357400.0
ATK = endpoint("00:00:00:00:00:04", "10.0.0.4", "s1", 4)
OTHER = endpoint("00:00:00:00:00:03", "10.0.0.3", "s1", 3)


def build_run(d: Path, labels, alerts, feats=(), actions=()):
    import json
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps({"v": 1, "run_id": d.name}), encoding="utf-8")
    for name, recs in (("labels.jsonl", labels), ("alerts_rule.jsonl", alerts),
                       ("features_1s.jsonl", feats), ("actions.jsonl", actions)):
        with open(d / name, "w", encoding="utf-8") as fh:
            for r in recs:
                write(fh, r)


def label(attack=ATK, start=T + 30, end=T + 60, atk="arp_spoof"):
    return make("label", ts=end, attack_id="a01", attack=atk, start_ts=start,
                end_ts=end, attacker=attack, target=None, evasive=False, params={})


def alert(ts, attacker=ATK, attack="arp_spoof"):
    return make("alert", ts=ts, alert_id=f"rule-{int(ts)}", detector="rule",
                source="x", attack=attack, score=1.0, attacker=attacker, victim=None,
                feature_ts=ts, win=1, summary="", evidence={})


class TestMetrics(unittest.TestCase):
    def eval(self, **kw):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "20260101-000000-arp_spoof"
            build_run(d, **kw)
            return evaluate.evaluate_run(d)["per_det"]["rule"]

    def test_true_positive(self):
        m = self.eval(labels=[label()], alerts=[alert(T + 45)])
        self.assertEqual((m["tp"], m["fp"], m["detected"]), (1, 0, 1))
        self.assertAlmostEqual(m["det_time"], 15.0)
        self.assertTrue(m["attributed"])

    def test_wrong_attacker_is_fp(self):
        # attack은 맞지만 공격자가 다름 → 틀린 경보
        m = self.eval(labels=[label()], alerts=[alert(T + 45, attacker=OTHER)])
        self.assertEqual((m["tp"], m["fp"], m["detected"]), (0, 1, 0))

    def test_normal_region_alert_is_fp(self):
        # 공격 구간 밖(정상)에서 난 경보 → FP
        m = self.eval(labels=[label()], alerts=[alert(T + 5)])
        self.assertEqual((m["tp"], m["fp"]), (0, 1))
        self.assertEqual(m["fp_normal"], 1)

    def test_grace_window(self):
        # 종료 직후 GRACE(5초) 안은 TP, 그 밖은 FP
        self.assertEqual(self.eval(labels=[label()], alerts=[alert(T + 63)])["tp"], 1)
        self.assertEqual(self.eval(labels=[label()], alerts=[alert(T + 66)])["fp"], 1)

    def test_null_attacker_detected_but_unattributed(self):
        # mac_flood: 공격자 mac null → 탐지(TP)는 되지만 공격자특정 X
        lab = label(atk="mac_flood")
        al = alert(T + 45, attacker=endpoint(None, None, None, None), attack="mac_flood")
        m = self.eval(labels=[lab], alerts=[al])
        self.assertEqual((m["tp"], m["fp"], m["detected"]), (1, 0, 1))
        self.assertFalse(m["attributed"])

    def test_detection_rate_partial(self):
        labs = [label(), label(atk="mac_flood", start=T + 100, end=T + 120)]
        m = self.eval(labels=labs, alerts=[alert(T + 45)])  # arp만 탐지
        self.assertEqual((m["detected"], m["attacks"]), (1, 2))

    def test_response_time_from_action(self):
        act = make("action", ts=T + 46, action="block", target=ATK, alert_id="rule-1",
                   reason="", expires_ts=None, ok=True, install_ms=2.0)
        m = self.eval(labels=[label()], alerts=[alert(T + 45)], actions=[act])
        self.assertAlmostEqual(m["resp_time"], 16.0)


if __name__ == "__main__":
    unittest.main()
