"""Caça ao Token: abre a janela e liga a tela ao Python."""
import json
import os
import sys
import threading
import time
import urllib.request
import webbrowser

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import epic  # noqa: E402
from catalog import Catalog, same_name  # noqa: E402
from tracker import Store, Tracker, looks_like_token  # noqa: E402

VERSION = "0.1.0"
REPO = "andreymira2/caca-ao-token"
EVENT_URL = f"https://raw.githubusercontent.com/{REPO}/main/data/evento.json"


def resource(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


class Api:
    """Tudo o que a tela pode pedir. Cada método devolve dados simples (JSON)."""

    def __init__(self, store=None, profile_source=None):
        self._store = store or Store()
        self._tracker = Tracker(self._store)
        self._catalog = Catalog(self._store)
        self._lock = threading.Lock()
        self._session = None
        self._error = None
        self._event = None
        self._profile_source = profile_source  # usado nos testes
        device = self._store.load("login.json", None)
        if device:
            self._session = epic.Session(device)

    # ---------- conta ----------
    def status(self):
        acc = self._store.load("conta.json", {})
        return {
            "version": VERSION,
            "logged_in": bool(self._session or self._profile_source),
            "name": acc.get("displayName"),
            "error": self._error,
            "data_folder": self._store.folder,
        }

    def open_login(self):
        webbrowser.open(epic.LOGIN_URL)
        return epic.LOGIN_URL

    def login(self, text):
        code = epic.extract_code(text)
        if not code:
            return {"ok": False, "error": "Não achei o código. Copie tudo o que aparece na página da Epic e cole aqui."}
        try:
            token = epic.token_from_code(code)
            device = epic.create_device_auth(token)
        except epic.EpicError as e:
            msg = str(e)
            if e.code and "authorization_code" in e.code:
                msg = "Esse código já venceu (dura uns 5 minutos e só vale uma vez). Gere outro."
            return {"ok": False, "error": msg}
        self._store.save("login.json", device)
        self._store.save("conta.json", {"displayName": token.get("displayName"), "accountId": token["account_id"]})
        self._session = epic.Session(device)
        self._error = None
        return {"ok": True, "name": token.get("displayName")}

    def logout(self):
        if self._session:
            try:
                epic.delete_device_auth(self._session.access(), self._session.device)
            except epic.EpicError:
                pass  # o arquivo local é apagado de qualquer jeito
        self._store.delete("login.json")
        self._store.delete("conta.json")
        self._session = None
        return True

    # ---------- dados ----------
    def refresh(self):
        with self._lock:
            try:
                if self._profile_source:
                    profile = self._profile_source()
                elif self._session:
                    profile = epic.query_profile(self._session.access())
                else:
                    return {"ok": False, "error": "Conecte sua conta Epic primeiro."}
            except epic.EpicError as e:
                if e.status in (400, 401) and e.code and "device" in e.code:
                    self._store.delete("login.json")
                    self._session = None
                    self._error = "O login venceu ou foi removido. Conecte de novo."
                else:
                    self._error = str(e)
                return {"ok": False, "error": self._error}
            self._error = None
            result = self._tracker.update(profile)
            return {"ok": True, **result,
                    "new_names": [self._catalog.name(t) or t for t in result["new_items"]]}

    def dashboard(self):
        return self._tracker.summary()

    def counters(self):
        return self._tracker.counters_view()

    def set_counter(self, key, on):
        self._tracker.set_selected(key, bool(on))
        return self._tracker.summary()

    def get_event(self):
        if self._event is None:
            try:
                req = urllib.request.Request(EVENT_URL, headers={"User-Agent": "CacaAoToken"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    self._event = json.loads(r.read().decode("utf-8"))
                    self._store.save("evento_cache.json", self._event)
            except Exception:
                cached = self._store.load("evento_cache.json", None)
                if cached is None:
                    with open(resource("data", "evento.json"), encoding="utf-8") as f:
                        cached = json.load(f)
                self._event = cached
        return self._event

    def prizes(self):
        """Prêmios da semana e fixos, com a marcação de quais já caíram na conta."""
        event = self.get_event()
        now = time.time()
        week = upcoming = None
        for w in event.get("semanas", []):
            if _ts(w["inicio"]) <= now < _ts(w["fim"]):
                week = w
            elif _ts(w["inicio"]) > now and upcoming is None:
                upcoming = w
        drop_names = []
        for d in self._tracker.state["drops"]:
            name = self._catalog.name(d["templateId"])
            drop_names.append({**d, "name": name, "token": looks_like_token(d["templateId"])})
        manual = self._tracker.state["manual_prizes"]

        def mark(p):
            def matches(d):
                if p.get("tipo") == "Token":
                    year = p["nome"][-4:]
                    return d["token"] and year in d["templateId"]
                return same_name(d["name"], p["nome"])
            hit = next((d for d in drop_names if matches(d)), None)
            return {**p, "obtido": bool(hit) or p["nome"] in manual,
                    "auto": bool(hit), "bau": hit["bau"] if hit else None}

        return {
            "semana": week and {**week, "premios": [mark(p) for p in week["premios"]]},
            "proxima": upcoming and {**upcoming, "premios": [mark(p) for p in upcoming["premios"]]},
            "fixos": [mark(p) for p in event.get("premios_fixos", [])],
            "historico": list(reversed(drop_names)),
        }

    def toggle_prize(self, name):
        return self._tracker.toggle_manual_prize(name)

    def export_diagnostics(self):
        self._store.save("diagnostico.json", self._tracker.diagnostics())
        self._store.save("itens.json", self._tracker.state.get("last_items") or {})
        self.open_data_folder()
        return self._store.folder

    def open_data_folder(self):
        if hasattr(os, "startfile"):
            os.startfile(self._store.folder)  # noqa: S606 (só existe no Windows)
        return self._store.folder


def _ts(iso):
    from datetime import datetime
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def main():
    import webview
    api = Api()
    webview.create_window("Caça ao Token", resource("ui", "index.html"), js_api=api,
                          width=1180, height=800, min_size=(900, 620), background_color="#0E1116")
    webview.start()


if __name__ == "__main__":
    main()
