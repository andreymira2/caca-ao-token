import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

import epic  # noqa: E402
from tracker import Store, Tracker, extract_counters, looks_like_token  # noqa: E402

KEY = "Quest:q_chests/completion_open"


def profile(chests, extra_items=()):
    items = {"q": {"templateId": "Quest:q_chests", "attributes": {"completion_open": chests, "creation_time": "x"}},
             "a": {"templateId": "AthenaCharacter:cid_1", "quantity": 1}}
    for i, tid in enumerate(extra_items):
        items[f"x{i}"] = {"templateId": tid, "quantity": 1}
    return {"items": items, "stats": {"attributes": {"book_level": 10, "flag": True}}}


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.clock = [1_762_500_000.0]
        self.t = Tracker(Store(tempfile.mkdtemp()), now=lambda: self.clock[0])

    def test_counters(self):
        c = extract_counters(profile(5))
        self.assertEqual(c[KEY], 5)
        self.assertEqual(c["stats/book_level"], 10)
        self.assertNotIn("stats/flag", c)

    def test_total_includes_value_at_selection_and_grows(self):
        self.t.update(profile(40))
        self.t.set_selected(KEY, True)
        self.assertEqual(self.t.total(), 40)
        self.clock[0] += 600
        self.assertEqual(self.t.update(profile(43))["gained"], 3)
        self.assertEqual(self.t.summary()["total"], 43)
        self.assertEqual(self.t.summary()["session"], 3)

    def test_counter_reset_keeps_counting(self):
        self.t.update(profile(10))
        self.t.set_selected(KEY, True)
        self.t.update(profile(2))  # quest semanal reiniciou e já tem 2 baús
        self.assertEqual(self.t.total(), 12)

    def test_drops_record_chest_number(self):
        self.t.update(profile(10))
        self.t.set_selected(KEY, True)
        r = self.t.update(profile(12, ["AthenaLoadingScreen:ls_x", "Quest:new_weekly", "Token:PirateShopAccess_2026"]))
        self.assertEqual(r["new_items"], ["AthenaLoadingScreen:ls_x", "Token:PirateShopAccess_2026"])
        self.assertEqual(r["token"], ["Token:PirateShopAccess_2026"])
        self.assertEqual(self.t.state["drops"][0]["bau"], 12)

    def test_state_survives_restart(self):
        self.t.update(profile(10))
        self.t.set_selected(KEY, True)
        t2 = Tracker(self.t.store)
        self.assertEqual(t2.total(), 10)

    def test_token_detection(self):
        self.assertTrue(looks_like_token("Token:pirate_shop_access_2027"))
        self.assertFalse(looks_like_token("AthenaCharacter:cid_pirate_captain"))

    def test_extract_code(self):
        code = "a" * 32
        self.assertEqual(epic.extract_code('{"redirectUrl":"x","authorizationCode":"%s","sid":null}' % code), code)
        self.assertEqual(epic.extract_code(code), code)
        self.assertIsNone(epic.extract_code("bobagem"))


if __name__ == "__main__":
    unittest.main()
