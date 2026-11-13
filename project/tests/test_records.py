"""common/records.py와 docs/data-format.md 검증.

실행 (project/ 폴더에서):  python -m unittest discover -s tests -v
"""

import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import (  # noqa: E402
    ATTACKS, SCHEMAS, endpoint, make, read, validate, write,
)

SAMPLE = ROOT / "docs" / "examples" / "run-sample"
DOC = ROOT / "docs" / "data-format.md"
T = 1763357430.0
H4 = endpoint("00:00:00:00:00:04", "10.0.0.4", "s1", 4)


def good(rtype):
    """종류별로 형식에 맞는 최소 기록."""
    if rtype == "label":
        return make("label", ts=T + 60, attack_id="a01", attack="arp_spoof",
                    start_ts=T, end_ts=T + 60, attacker=H4, target=None,
                    evasive=False, params={})
    if rtype == "feat_host":
        return make("feat_host", ts=T, win=1, host=H4)
    if rtype == "feat_seg":
        return make("feat_seg", ts=T, win=5, sw="s1", port=4)
    if rtype == "alert":
        return make("alert", ts=T, alert_id="rule-1", detector="rule", source="r",
                    attack="arp_spoof", score=1.0, attacker=H4, victim=None,
                    feature_ts=T, win=1, summary="", evidence={})
    if rtype == "action":
        return make("action", ts=T, action="block", target=H4, alert_id=None,
                    reason="", expires_ts=None, ok=True, install_ms=1.0)
    raise KeyError(rtype)


def errs_with(rec, **changes):
    rec = json.loads(json.dumps(rec))
    for k, v in changes.items():
        if v is ...:
            rec.pop(k, None)
        else:
            rec[k] = v
    return validate(rec)


class TestValidRecords(unittest.TestCase):
    def test_every_type_builds_and_validates(self):
        for rtype in SCHEMAS:
            with self.subTest(rtype=rtype):
                self.assertEqual(validate(good(rtype)), [])

    def test_feature_defaults_are_zero(self):
        rec = good("feat_host")
        self.assertEqual(rec["arp_rep"], 0)
        self.assertEqual(rec["extra"], {})

    def test_all_attack_types_accepted_in_alert(self):
        for a in ATTACKS:
            with self.subTest(attack=a):
                self.assertEqual(errs_with(good("alert"), attack=a), [])

    def test_unknown_values_may_be_null(self):
        rec = good("feat_seg")
        self.assertEqual(errs_with(rec, sw=None, port=None), [])
        ep = endpoint("00:00:00:00:00:04")
        self.assertEqual(errs_with(good("alert"), attacker=ep), [])

    def test_endpoint_lowercases_mac(self):
        self.assertEqual(endpoint("AA:BB:CC:DD:EE:FF")["mac"], "aa:bb:cc:dd:ee:ff")

    def test_extra_holds_model_features(self):
        rec = make("feat_host", ts=T, win=1, host=H4, extra={"kitsune_0": 0.5})
        self.assertEqual(validate(rec), [])


class TestInvalidRecords(unittest.TestCase):
    def assertRejected(self, rec, **changes):
        errs = errs_with(rec, **changes)
        self.assertTrue(errs, f"통과하면 안 됨: {changes}")
        return errs

    def test_common_fields(self):
        r = good("alert")
        self.assertRejected(r, v=2)
        self.assertRejected(r, type="alarm")
        self.assertRejected(r, ts=...)
        self.assertRejected(r, ts="1763357430")
        self.assertRejected(r, ts=True)
        self.assertRejected(r, ts=1763357430123)      # 밀리초
        self.assertRejected(r, ts=12.5)               # 상대 시각
        self.assertEqual(validate([1, 2]), ["기록은 JSON 객체여야 함"])

    def test_other_time_fields_checked_like_ts(self):
        self.assertRejected(good("label"), start_ts=1763357430000)
        self.assertRejected(good("alert"), feature_ts=3.0)
        self.assertRejected(good("action"), expires_ts=1763357430000)

    def test_missing_field(self):
        for rtype, rec in ((t, good(t)) for t in SCHEMAS):
            for field in SCHEMAS[rtype]:
                with self.subTest(rtype=rtype, field=field):
                    self.assertRejected(rec, **{field: ...})

    def test_unknown_top_level_field_rejected(self):
        # 오타(arp_reps)가 조용히 0으로 바뀌는 사고를 막음
        errs = self.assertRejected(good("feat_host"), arp_reps=3)
        self.assertTrue(any("arp_reps" in e for e in errs))
        with self.assertRaises(ValueError):
            make("feat_host", ts=T, win=1, host=H4, arp_reps=3)

    def test_wrong_types(self):
        self.assertRejected(good("feat_host"), pkts=2.0)
        self.assertRejected(good("feat_host"), pkts="2")
        self.assertRejected(good("feat_host"), pkts=True)
        self.assertRejected(good("label"), evasive=1)
        self.assertRejected(good("alert"), evidence=[])
        self.assertRejected(good("action"), ok="true")

    def test_enums(self):
        self.assertRejected(good("alert"), attack="arp_spoofing")
        self.assertRejected(good("alert"), detector="ml")
        self.assertRejected(good("action"), action="drop")
        self.assertRejected(good("label"), attack="normal")

    def test_ranges(self):
        self.assertRejected(good("feat_host"), win=3)
        self.assertRejected(good("feat_host"), pkts=-1)
        self.assertRejected(good("feat_host"), top_dst_share=1.5)
        self.assertRejected(good("alert"), score=1.01)
        self.assertRejected(good("alert"), score=-0.1)
        self.assertRejected(good("label"), start_ts=T + 100)   # 끝보다 늦은 시작

    def test_endpoint(self):
        a = good("alert")
        ep = dict(H4)
        self.assertRejected(a, attacker=None)
        self.assertRejected(a, attacker="00:00:00:00:00:04")
        self.assertRejected(a, attacker={k: v for k, v in ep.items() if k != "port"})
        self.assertRejected(a, attacker={**ep, "mac": "00-00-00-00-00-04"})
        self.assertRejected(a, attacker={**ep, "mac": "00:00:00:00:00:0A"})
        self.assertRejected(a, attacker={**ep, "mac": "zz:00:00:00:00:04"})
        self.assertRejected(a, attacker={**ep, "mac": "0:0:0:0:0:4"})
        self.assertRejected(a, attacker={**ep, "port": "4"})
        self.assertRejected(a, attacker={**ep, "port": True})

    def test_make_raises(self):
        with self.assertRaises(ValueError):
            make("alert", ts=T)


class TestFileIO(unittest.TestCase):
    def test_round_trip_with_korean(self):
        rec = make("alert", **{**good("alert"), "summary": "게이트웨이 사칭"})
        buf = io.StringIO()
        write(buf, rec)
        line = buf.getvalue()
        self.assertTrue(line.endswith("\n"))
        self.assertEqual(line.count("\n"), 1)
        self.assertIn("게이트웨이", line)          # \uXXXX로 바뀌지 않음
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.jsonl"
            p.write_text(line + "\n", encoding="utf-8")   # 빈 줄 포함
            self.assertEqual(list(read(p)), [rec])

    def test_read_utf8_bom(self):
        # PowerShell의 Out-File은 BOM을 붙여 저장함
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.jsonl"
            p.write_text(json.dumps(good("label")) + "\n", encoding="utf-8-sig")
            self.assertEqual(len(list(read(p))), 1)


class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "common" / "records.py"), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_sample_folder_passes(self):
        r = self.run_cli("check", str(SAMPLE))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.count("통과"), 5)

    def test_bad_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.jsonl"
            p.write_text('{"v":1}\nnot json\n', encoding="utf-8")
            r = self.run_cli("check", str(p))
            self.assertEqual(r.returncode, 1)
            self.assertIn("bad.jsonl:2: JSON 오류", r.stdout)

    def test_bom_file_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.jsonl"
            p.write_text(json.dumps(good("label")) + "\n", encoding="utf-8-sig")
            self.assertEqual(self.run_cli("check", str(p)).returncode, 0)

    def test_missing_path_and_empty_folder(self):
        r = self.run_cli("check", "no/such/file.jsonl")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("check", d)
            self.assertEqual(r.returncode, 2)

    def test_usage(self):
        self.assertEqual(self.run_cli().returncode, 2)


class TestDocMatchesCode(unittest.TestCase):
    """data-format.md 표의 필드 = records.py SCHEMAS의 필드."""

    SECTIONS = {"label": "2.1", "feat_host": "2.2", "feat_seg": "2.3",
                "alert": "2.4", "action": "2.5"}
    COMMON = {"ts", "v", "type"}

    @classmethod
    def setUpClass(cls):
        cls.doc = DOC.read_text(encoding="utf-8")

    def doc_fields(self, sec):
        part = self.doc.split(f"### {sec} ", 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
        fields = set()
        for line in part.splitlines():
            m = re.match(r"\|\s*(`[^|]+`)\s*\|", line)
            if m:
                fields |= set(re.findall(r"`(\w+)`", m.group(1)))
        return fields

    def test_fields_match(self):
        for rtype, sec in self.SECTIONS.items():
            with self.subTest(rtype=rtype):
                doc = self.doc_fields(sec) - self.COMMON
                if rtype == "feat_seg":       # "feat_host와 같음"으로 적은 win
                    doc.add("win")
                code = set(SCHEMAS[rtype])
                self.assertEqual(doc, code, f"문서에만: {doc - code}, 코드에만: {code - doc}")

    def test_attack_list_matches(self):
        part = self.doc.split("### 공격 종류", 1)[1].split("\n### ", 1)[0]
        doc = set(re.findall(r"^\|\s*`(\w+)`", part, re.M))
        self.assertEqual(doc, ATTACKS)


class TestSampleRunIsConsistent(unittest.TestCase):
    """예시 실험이 4장 평가 기준대로 말이 되는지."""

    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((SAMPLE / "meta.json").read_text(encoding="utf-8"))
        cls.labels = list(read(SAMPLE / "labels.jsonl"))
        cls.alerts = list(read(SAMPLE / "alerts.jsonl"))
        cls.actions = list(read(SAMPLE / "actions.jsonl"))
        cls.feats = list(read(SAMPLE / "features_1s.jsonl")) + list(read(SAMPLE / "features_5s.jsonl"))

    def test_type_per_file(self):
        self.assertTrue(all(r["type"] == "label" for r in self.labels))
        self.assertTrue(all(r["type"] == "alert" for r in self.alerts))
        self.assertTrue(all(r["type"] == "action" for r in self.actions))
        self.assertTrue(all(r["type"] in ("feat_host", "feat_seg") for r in self.feats))
        self.assertTrue(all(r["win"] == 1 for r in read(SAMPLE / "features_1s.jsonl")))
        self.assertTrue(all(r["win"] == 5 for r in read(SAMPLE / "features_5s.jsonl")))

    def test_all_times_inside_run(self):
        s, e = self.meta["start_ts"], self.meta["end_ts"]
        for r in self.labels + self.alerts + self.actions + self.feats:
            self.assertTrue(s <= r["ts"] <= e, r)

    def test_attacker_matches_meta(self):
        att = [h for h in self.meta["hosts"] if h["role"] == "attacker"]
        self.assertEqual(len(att), 1)
        for lab in self.labels:
            self.assertEqual(lab["attacker"]["mac"], att[0]["mac"])

    def test_meta_hosts_unique(self):
        hosts = self.meta["hosts"]
        for key in ("name", "mac", "ip", "port"):
            vals = [h[key] for h in hosts]
            self.assertEqual(len(vals), len(set(vals)), key)

    def test_alerts_are_true_positives(self):
        for a in self.alerts:
            hit = [l for l in self.labels if l["attack"] == a["attack"]
                   and l["start_ts"] <= a["ts"] <= l["end_ts"] + 5
                   and l["attacker"]["mac"] == a["attacker"]["mac"]]
            self.assertTrue(hit, a["alert_id"])

    def test_alert_points_to_existing_feature(self):
        keys = {(f["ts"], f["win"]) for f in self.feats}
        for a in self.alerts:
            self.assertIn((a["feature_ts"], a["win"]), keys, a["alert_id"])
            self.assertGreaterEqual(a["ts"], a["feature_ts"])   # 특징이 먼저

    def test_action_follows_its_alert(self):
        by_id = {a["alert_id"]: a for a in self.alerts}
        for act in self.actions:
            if act["alert_id"] is not None:
                al = by_id[act["alert_id"]]
                self.assertGreater(act["ts"], al["ts"])
                self.assertEqual(act["target"]["mac"], al["attacker"]["mac"])

    def test_latency_numbers(self):
        lab = self.labels[0]
        first = min(a["ts"] for a in self.alerts)
        block = min(x["ts"] for x in self.actions if x["action"] == "block")
        self.assertAlmostEqual(first - lab["start_ts"], 1.02, places=6)
        self.assertAlmostEqual(block - lab["start_ts"], 1.08, places=6)


if __name__ == "__main__":
    unittest.main()
