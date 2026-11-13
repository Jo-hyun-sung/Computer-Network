"""model/dataset.py 라벨링 검증 (scikit-learn 불필요)."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.records import endpoint, make  # noqa: E402
from model import dataset  # noqa: E402

T = 1763357400.0
ATK = endpoint("00:00:00:00:00:04", "10.0.0.4", "s1", 4)
H1 = endpoint("00:00:00:00:00:01", "10.0.0.1", "s1", 1)


def feat(mac_ep, ts, **kw):
    return make("feat_host", ts=ts, win=1, host=mac_ep, **kw)


def lab(attack="arp_spoof", attacker=ATK, start=T + 30, end=T + 60):
    return make("label", ts=end, attack_id="a01", attack=attack, start_ts=start,
                end_ts=end, attacker=attacker, target=None, evasive=False, params={})


class TestLabeling(unittest.TestCase):
    def test_attacker_in_window_is_attack(self):
        self.assertEqual(dataset.label_for(feat(ATK, T + 45), [lab()]), "arp_spoof")

    def test_other_host_in_window_is_normal(self):
        self.assertEqual(dataset.label_for(feat(H1, T + 45), [lab()]), "normal")

    def test_attacker_outside_window_is_normal(self):
        self.assertEqual(dataset.label_for(feat(ATK, T + 10), [lab()]), "normal")

    def test_mac_flood_not_host_attributable(self):
        # 플러딩은 가짜 MAC → 호스트 라벨에서 공격으로 보지 않음
        l = lab(attack="mac_flood")
        self.assertEqual(dataset.label_for(feat(ATK, T + 45), [l]), "normal")

    def test_no_labels_all_normal(self):
        self.assertEqual(dataset.label_for(feat(ATK, T + 45), []), "normal")

    def test_feature_vector_length_matches(self):
        rec = feat(ATK, T + 45, arp_ip_conflicts=1)
        vec = [float(rec.get(k, 0) or 0) for k in dataset.FEATURES]
        self.assertEqual(len(vec), len(dataset.FEATURES))
        self.assertEqual(vec[dataset.FEATURES.index("arp_ip_conflicts")], 1.0)


if __name__ == "__main__":
    unittest.main()
