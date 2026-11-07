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
        path = api.lab_export()
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
