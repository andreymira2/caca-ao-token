import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

import main  # noqa: E402
from tracker import Store  # noqa: E402

ACC = "a1b2c3d4e5f60718293a4b5c6d7e8f90"


class ExportTest(unittest.TestCase):
    def test_zip_has_profiles_without_account_id(self):
        n = [100]

        def profile():
            n[0] += 4
            return {"accountId": ACC, "items": {"q": {"templateId": "Quest:q_chests",
                    "attributes": {"completion_open_chests": n[0], "owner": ACC}}},
                    "stats": {"attributes": {"some_new_field": n[0] * 2}}}

        store = Store(tempfile.mkdtemp())
        store.save("conta.json", {"accountId": ACC, "displayName": "AndreyTeste"})
        api = main.Api(store=store, profile_source=profile)
        api._event = {"semanas": [], "agenda": []}
        self.assertTrue(api.lab_start()["ok"])
        res = api.lab_finish(4, 0, 0)
        self.assertTrue(res["ok"])
        self.assertEqual(res["result"]["rows"][0]["match"], ["total"])
        path = api.lab_export()["path"]
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            self.assertIn("relatorio.json", names)
            self.assertEqual(len([x for x in names if x.startswith("perfis/")]), 2)
            blob = b"".join(z.read(x) for x in names)
        self.assertNotIn(ACC.encode(), blob)
        self.assertNotIn(b"AndreyTeste", blob)
        self.assertIn(b"some_new_field", blob)


if __name__ == "__main__":
    unittest.main()


class LocalFilesTest(unittest.TestCase):
    def test_log_excerpt_window_and_redaction(self):
        import localfiles
        from datetime import datetime, timezone
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "Logs"))
        t0 = datetime(2026, 11, 7, 15, 50, 0, tzinfo=timezone.utc).timestamp()
        with open(os.path.join(d, "Logs", "FortniteGame.log"), "w", encoding="utf-8") as f:
            f.write("[2026.11.07-14.00.00:000][  1]LogX: antes da partida\n")
            f.write(f"[2026.11.07-15.51.00:000][  2]LogFort: Container opened by AndreyTeste {ACC} from 10.0.0.5:7777\n")
            f.write("continuação sem hora\n")
            f.write("[2026.11.07-18.00.00:000][  3]LogX: depois\n")
        out = localfiles.log_excerpt([(t0, t0 + 300)], (ACC, "AndreyTeste"), folder=d)
        self.assertIn("Container opened by <conta>", out)
        self.assertIn("continuação sem hora", out)
        self.assertNotIn("antes da partida", out)
        self.assertNotIn("10.0.0.5", out)
        self.assertNotIn(ACC, out)
