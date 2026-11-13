"""dashboard/load.py, notify.py 검증 (Streamlit 불필요)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import endpoint, make, write  # noqa: E402
from dashboard import load, notify  # noqa: E402

T = 1763357400.0
ATK = endpoint("00:00:00:00:00:04", "10.0.0.4", "s1", 4)


def build(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps({
        "v": 1, "run_id": d.name, "scenario": "arp_spoof",
        "hosts": [{"name": "h4", "role": "attacker", **ATK}]}), encoding="utf-8")
    with open(d / "labels.jsonl", "w", encoding="utf-8") as fh:
        write(fh, make("label", ts=T + 60, attack_id="a01", attack="arp_spoof",
                       start_ts=T + 30, end_ts=T + 60, attacker=ATK, target=None,
                       evasive=False, params={}))
    with open(d / "alerts_rule.jsonl", "w", encoding="utf-8") as fh:
        write(fh, make("alert", ts=T + 45, alert_id="rule-1", detector="rule",
                       source="arp_conflict", attack="arp_spoof", score=1.0,
                       attacker=ATK, victim=None, feature_ts=T + 45, win=1,
                       summary="게이트웨이 사칭", evidence={}))
    with open(d / "alerts_ai.jsonl", "w", encoding="utf-8") as fh:
        write(fh, make("alert", ts=T + 46, alert_id="ai-1", detector="ai",
                       source="rf-v1", attack="arp_spoof", score=0.93,
                       attacker=ATK, victim=None, feature_ts=T + 46, win=5,
                       summary="AI 유사", evidence={}))


class TestLoad(unittest.TestCase):
    def test_summary_counts_detectors(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "20260101-000000-arp_spoof"
            build(d)
            s = load.summarize(d)
            self.assertEqual(s["n_alerts"], 2)
            self.assertEqual(s["by_detector"], {"rule": 1, "ai": 1})
            self.assertEqual(s["attacks"], ["arp_spoof"])

    def test_alert_rows_sorted_and_fielded(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "20260101-000000-arp_spoof"
            build(d)
            rows = load.alert_rows(d)
            self.assertEqual(len(rows), 2)
            self.assertLessEqual(rows[0]["시각"], rows[1]["시각"])  # 시각순
            self.assertEqual(rows[0]["공격자MAC"], "00:00:00:00:00:04")
            self.assertIn("탐지기", rows[0])

    def test_list_runs_reverse_order(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            for name in ("20260101-000000-a", "20260102-000000-b"):
                build(base / name)
            runs = load.list_runs(base)
            self.assertEqual([r.name for r in runs],
                             ["20260102-000000-b", "20260101-000000-a"])

    def test_missing_files_safe(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "empty"
            d.mkdir()
            self.assertEqual(load.load_alerts(d), [])
            self.assertEqual(load.load_meta(d), {})


class TestNotify(unittest.TestCase):
    def alert(self, attack="arp_spoof"):
        return make("alert", ts=T + 45, alert_id="rule-1", detector="rule",
                    source="x", attack=attack, score=0.93, attacker=ATK, victim=None,
                    feature_ts=T + 45, win=1, summary="사칭 탐지", evidence={})

    def test_payload_structure(self):
        p = notify.format_alert(self.alert())
        self.assertIn("embeds", p)
        emb = p["embeds"][0]
        self.assertIn("arp_spoof", emb["title"])
        self.assertEqual(emb["description"], "사칭 탐지")
        names = {f["name"] for f in emb["fields"]}
        self.assertEqual(names, {"탐지기", "확신도", "공격자"})

    def test_color_differs_by_attack(self):
        c1 = notify.format_alert(self.alert("arp_spoof"))["embeds"][0]["color"]
        c2 = notify.format_alert(self.alert("mac_flood"))["embeds"][0]["color"]
        self.assertNotEqual(c1, c2)

    def test_confidence_percent(self):
        emb = notify.format_alert(self.alert())["embeds"][0]
        conf = next(f["value"] for f in emb["fields"] if f["name"] == "확신도")
        self.assertEqual(conf, "93%")


if __name__ == "__main__":
    unittest.main()
