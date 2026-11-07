import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

import epic  # noqa: E402
from tracker import Store, Tracker, extract_counters, looks_like_token  # noqa: E402

KEY = "Quest:q_chests/completion_open"
OTHER = "Quest:q_elims/completion_elims"


def profile(chests, extra_items=()):
    items = {"q": {"templateId": "Quest:q_chests", "attributes": {"completion_open": chests, "creation_time": "x"}},
             "e": {"templateId": "Quest:q_elims", "attributes": {"completion_elims": 7}},
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
        self.t.set_counter(KEY)
        self.assertEqual(self.t.total(), 40)
        self.clock[0] += 600
        self.assertEqual(self.t.update(profile(43))["gained"], 3)
        self.assertEqual(self.t.summary()["total"], 43)
        self.assertEqual(self.t.summary()["session"], 3)

    def test_counter_reset_keeps_counting(self):
        self.t.update(profile(10))
        self.t.set_counter(KEY)
        self.t.update(profile(2))  # quest semanal reiniciou e já tem 2 baús
        self.assertEqual(self.t.total(), 12)

    def test_drops_record_chest_number(self):
        self.t.update(profile(10))
        self.t.set_counter(KEY)
        r = self.t.update(profile(12, ["AthenaLoadingScreen:ls_x", "Quest:new_weekly", "Token:PirateShopAccess_2026"]))
        self.assertEqual(r["new_items"], ["AthenaLoadingScreen:ls_x", "Token:PirateShopAccess_2026"])
        self.assertEqual(r["token"], ["Token:PirateShopAccess_2026"])
        self.assertEqual(self.t.state["drops"][0]["bau"], 12)

    def test_state_survives_restart(self):
        self.t.update(profile(10))
        self.t.set_counter(KEY)
        t2 = Tracker(self.t.store)
        self.assertEqual(t2.total(), 10)

    def test_auto_picks_chest_counter_unconfirmed(self):
        self.t.update(profile(40))
        c = self.t.state["counter"]
        self.assertEqual(c["key"], KEY)
        self.assertFalse(c["confirmed"])
        self.assertEqual(self.t.total(), 40)

    def test_find_by_game_number(self):
        self.t.update(profile(40))
        self.assertEqual([h["key"] for h in self.t.find_by_value(40)], [KEY])
        self.assertEqual([h["key"] for h in self.t.find_by_value(7)], [OTHER])
        self.assertEqual(self.t.find_by_value(10), [])  # stats/book_level nunca entra

    def test_stats_cannot_be_counter(self):
        self.t.update(profile(1))
        with self.assertRaises(ValueError):
            self.t.set_counter("stats/book_level")

    def test_old_multi_counter_state_is_reset(self):
        self.t.store.save("estado.json", {**self.t.state, "selected": {"stats/book_level": {"total": 2444, "last": 10}}})
        t2 = Tracker(self.t.store)
        self.assertEqual(t2.total(), 0)
        self.assertNotIn("selected", t2.state)

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


class EventTracksTest(unittest.TestCase):
    def quest(self, kind, n, value, state):
        return {"templateId": f"Quest:quest_s43_treasurehunt_{kind}_0{n}",
                "attributes": {f"completion_quest_s43_treasurehunt_{kind}_0{n}_obj0": value, "quest_state": state}}

    def test_total_is_max_across_goals_and_cap(self):
        from tracker import event_tracks
        prof = {"items": {"a": self.quest("count", 1, 25, "Claimed"), "b": self.quest("count", 2, 100, "Claimed"),
                          "c": self.quest("count", 3, 137, "Active"), "d": self.quest("sprites", 5, 74, "Active"),
                          "e": self.quest("rarity", 5, 100, "Claimed")}}
        t = event_tracks(prof)
        self.assertEqual(t["total"], {"value": 137, "quests": 3, "capped": False})
        self.assertTrue(t["raros"]["capped"])
        self.assertEqual(t["sprite"]["value"], 74)

    def test_tracker_uses_event_total_over_old_guess(self):
        tr = Tracker(Store(tempfile.mkdtemp()))
        tr.state["counter"] = {"key": "Quest:quest_s43_spritebackbling_treasurechest/completion_x", "total": 1,
                               "last": 1, "confirmed": False}
        tr.update({"items": {"c": self.quest("count", 3, 137, "Active")}})
        self.assertEqual((tr.state["counter"]["key"], tr.total()), ("evento/total", 137))
        tr.update({"items": {"c": self.quest("count", 3, 140, "Active")}})
        self.assertEqual(tr.total(), 140)
