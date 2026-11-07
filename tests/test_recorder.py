import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

from recorder import Recorder, _pattern  # noqa: E402
from tracker import Store, Tracker  # noqa: E402

CH = "Quest:quest_s39_th_chests/completion_open_chests"
RARE = "Quest:quest_s39_th_rare/completion_open_rare"
XP = "stats/book_xp"


class RecorderTest(unittest.TestCase):
    def setUp(self):
        self.clock = [1_762_500_000.0]
        self.r = Recorder(Store(tempfile.mkdtemp()), lambda: self.clock[0])

    def run_test(self, before, after, **declared):
        self.r.start(before)
        self.clock[0] += 900
        return self.r.finish(after, declared)

    def test_matching_counter_ranks_first(self):
        res = self.run_test({CH: 1000, RARE: 50, XP: 10}, {CH: 1007, RARE: 52, XP: 17}, total=7, raros=2)
        self.assertEqual(res["rows"][0]["key"], CH)
        self.assertIn("total", res["rows"][0]["match"])
        # Na primeira partida o XP também subiu 7: empata. Na segunda, separa.
        self.run_test({CH: 1007, RARE: 52, XP: 17}, {CH: 1012, RARE: 53, XP: 30}, total=5, raros=1)
        rank = self.r.ranking()
        self.assertEqual(rank["total"][0], {"key": CH, "hits": 2, "moved": 2, "tests": 2})
        self.assertEqual(rank["raros"][0]["key"], RARE)

    def test_report_suggests_only_perfect_counters(self):
        self.run_test({CH: 1}, {CH: 4}, total=3)
        rep = self.r.report({CH: 4}, None)
        self.assertEqual(rep["sugestao_padrao"]["total"]["chave"], CH)
        self.assertNotIn("conta", str(rep).lower().replace("contador", ""))

    def test_pattern_generalises_numbers(self):
        import re
        pat = _pattern(CH)
        self.assertTrue(re.fullmatch(pat, "Quest:quest_s40_th_chests/completion_open_chests"))

    def test_observe_logs_changes(self):
        self.r.observe({CH: 1}, {CH: 3})
        self.assertEqual(self.r.recent()[0]["delta"], 2)


class PresetTest(unittest.TestCase):
    def test_preset_is_used_and_confirmed(self):
        t = Tracker(Store(tempfile.mkdtemp()))
        t.presets = [_pattern(CH)]
        t.update({"items": {"q": {"templateId": "Quest:quest_s39_th_chests",
                                  "attributes": {"completion_open_chests": 1200}}}})
        c = t.state["counter"]
        self.assertEqual((c["key"], c["confirmed"], c["source"]), (CH, True, "padrao"))
        self.assertEqual(t.total(), 1200)


if __name__ == "__main__":
    unittest.main()
