"""Testa a tela no navegador com uma conta falsa: python tools/dev_server.py

Abre http://127.0.0.1:8765. Cada "Atualizar" simula alguns baús abertos.
"""
import json
import os
import random
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from main import Api  # noqa: E402
from tracker import Store  # noqa: E402


class FakeAccount:
    def __init__(self):
        self.chests = 37
        self.calls = 0
        self.items = {f"i{n}": {"templateId": f"AthenaCharacter:cid_{n:03d}", "quantity": 1} for n in range(40)}

    def profile(self):
        self.calls += 1
        if self.calls > 1:
            self.chests += random.randint(1, 6)
        if self.calls == 3:
            self.items["new1"] = {"templateId": "AthenaLoadingScreen:lsid_sokawaii", "quantity": 1}
        if os.environ.get("FAKE_TOKEN") and self.calls == 4:
            self.items["tok"] = {"templateId": "Token:pirateshopaccess_2026", "quantity": 1}
        items = dict(self.items)
        items["q1"] = {"templateId": "Quest:quest_s39_treasurehunters_open_chests",
                       "attributes": {"completion_open_treasure_chests": self.chests}}
        items["q2"] = {"templateId": "Quest:quest_s39_weekly_eliminations",
                       "attributes": {"completion_elims": 4 + self.calls}}
        items["q3"] = {"templateId": "Quest:quest_s39_mapfragment_w2",
                       "attributes": {"completion_collect_map_fragment": 1}}
        return {"items": items, "stats": {"attributes": {"book_level": 61, "accountLevel": 412, "season_num": 39}}}


folder = tempfile.mkdtemp(prefix="caca-dev-")
api = Api(store=Store(folder), profile_source=FakeAccount().profile)
api._catalog.names.update({"AthenaLoadingScreen:lsid_sokawaii": "So Kawaii"})

MOCK_JS = b"""
window.MOCK_API = new Proxy({}, { get: (_, name) => async (...args) => {
  const r = await fetch('/api/' + name, { method: 'POST', body: JSON.stringify(args) });
  return r.json();
}});
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="application/json", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(ROOT, "ui", "index.html"), "rb") as f:
                return self._send(f.read(), "text/html; charset=utf-8")
        if self.path == "/mock.js":
            return self._send(MOCK_JS, "text/javascript")
        self._send(b"", code=404)

    def do_POST(self):
        name = self.path.rsplit("/", 1)[-1]
        args = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or "[]")
        if name.startswith("_") or not hasattr(api, name):
            return self._send(b"null", code=404)
        if name in ("open_login", "open_data_folder"):
            return self._send(b"null")
        result = getattr(api, name)(*args)
        self._send(json.dumps(result).encode())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    print(f"http://127.0.0.1:{port}  (dados em {folder})")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
