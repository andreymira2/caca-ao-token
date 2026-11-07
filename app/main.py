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
from recorder import Recorder  # noqa: E402
from tracker import Store, Tracker, looks_like_token  # noqa: E402

VERSION = "0.4.0"
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
        self._recorder = Recorder(self._store, self._tracker.now)
        self._lock = threading.Lock()
        self._session = None
        self._error = None
        self._event = None
        self._profile_source = profile_source  # usado nos testes
        self._last_profile = None
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
            event = self.get_event()
            presets = [c["padrao"] for c in event.get("contadores_padrao", [])
                       if c.get("tipo") == "total" and c.get("padrao")]
            if presets:
                self._tracker.presets = presets
            for kind, pat in (event.get("trilhas_baus") or {}).items():
                self._tracker.tracks[kind] = pat
            self._last_profile = profile
            result = self._tracker.update(profile)
            self._recorder.observe(self._tracker.prev_counters, self._tracker.state["last_counters"])
            return {"ok": True, **result,
                    "new_names": [(self._catalog.item(t) or {}).get("name") or t for t in result["new_items"]]}

    def dashboard(self):
        return self._tracker.summary()

    def counters(self):
        return self._tracker.counters_view()

    def chest_check(self):
        """O que a tela precisa para conferir o contador de baús."""
        return {"counter": self._tracker.state["counter"],
                "candidates": self._tracker.chest_candidates()[:6]}

    def find_counter(self, game_number):
        """Procura o contador com o mesmo número que o jogo mostra."""
        try:
            n = int(str(game_number).replace(".", "").strip())
        except ValueError:
            return {"ok": False, "error": "Digite só o número, por exemplo 214."}
        hits = self._tracker.find_by_value(n)
        if len(hits) == 1 or (hits and hits[0]["chest"] and not any(h["chest"] for h in hits[1:])):
            self._tracker.set_counter(hits[0]["key"], confirmed=True)
            return {"ok": True, "matched": True, "summary": self._tracker.summary()}
        return {"ok": True, "matched": False, "hits": hits}

    def set_counter(self, key):
        self._tracker.set_counter(key, confirmed=True)
        return self._tracker.summary()

    def confirm_counter(self):
        self._tracker.confirm_counter()
        return self._tracker.summary()

    def reset_counter(self):
        self._tracker.reset_counter()
        return self._tracker.summary()

    def get_event(self):
        if self._event is None:
            with open(resource("data", "evento.json"), encoding="utf-8") as f:
                bundled = json.load(f)
            try:
                req = urllib.request.Request(EVENT_URL, headers={"User-Agent": "CacaAoToken"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    online = json.loads(r.read().decode("utf-8"))
                    self._store.save("evento_cache.json", online)
            except Exception:
                online = self._store.load("evento_cache.json", None)
            # Usa a lista online só se ela for igual ou mais nova que a que veio no app.
            ok = online and online.get("versao", 0) >= bundled.get("versao", 0)
            self._event = online if ok else bundled
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
            info = self._catalog.item(d["templateId"]) or {}
            drop_names.append({**d, "name": info.get("name"), "image": info.get("image"),
                               "rarity": info.get("rarity"), "token": looks_like_token(d["templateId"])})
        manual = self._tracker.state["manual_prizes"]

        def mark(p):
            def matches(d):
                if p.get("tipo") == "Token":
                    year = p["nome"][-4:]
                    return d["token"] and year in d["templateId"]
                if p.get("id") and d["templateId"].split(":", 1)[-1].lower() == p["id"].lower():
                    return True
                return same_name(d["name"], p["nome"])
            hit = next((d for d in drop_names if matches(d)), None)
            info = (self._catalog.prize(p) if p.get("tipo") != "Token" else None) or {}
            return {**p, "obtido": bool(hit) or p["nome"] in manual,
                    "auto": bool(hit), "bau": hit["bau"] if hit else None,
                    "image": info.get("image"), "rarity": info.get("rarity") or p.get("raridade")}

        return {
            "semana": week and {**week, "premios": [mark(p) for p in week["premios"]]},
            "proxima": upcoming and {**upcoming, "premios": [mark(p) for p in upcoming["premios"]]},
            "fixos": [mark(p) for p in event.get("premios_fixos", [])],
            "historico": list(reversed(drop_names)),
        }

    # ---------- rastreador ----------
    def _profiles_snapshot(self):
        """Perfil completo (athena e common_core), sem o ID e o nome da conta."""
        profiles = {"athena": self._last_profile}
        if self._session and not self._profile_source:
            try:
                profiles["common_core"] = epic.query_profile(self._session.access(), "common_core")
            except epic.EpicError:
                pass
        acc = self._store.load("conta.json", {})
        text = json.dumps(profiles, ensure_ascii=False)
        for prof in profiles.values():
            if isinstance(prof, dict):
                prof.pop("_id", None)
        for secret in (acc.get("accountId"), acc.get("displayName")):
            if secret:
                text = text.replace(secret, "<conta>")
        return json.loads(text)

    def lab_state(self):
        return {**self._recorder.state(), "counter": self._tracker.state["counter"]}

    def lab_start(self):
        r = self.refresh()
        if not r.get("ok"):
            return r
        self._recorder.start(self._tracker.state["last_counters"], self._profiles_snapshot())
        return {"ok": True, **self.lab_state()}

    def lab_finish(self, total, raros=0, sprite=0):
        try:
            declared = {"total": int(total or 0), "raros": int(raros or 0), "sprite": int(sprite or 0)}
        except ValueError:
            return {"ok": False, "error": "Use só números."}
        r = self.refresh()
        if not r.get("ok"):
            return r
        try:
            result = self._recorder.finish(self._tracker.state["last_counters"], declared,
                                           self._profiles_snapshot())
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "result": result, **self.lab_state()}

    def lab_cancel(self):
        self._recorder.cancel()
        return self.lab_state()

    def lab_delete(self, index):
        # A tela lista do mais novo para o mais antigo.
        self._recorder.delete_test(len(self._recorder.data["tests"]) - 1 - int(index))
        return self.lab_state()

    def lab_use(self, key):
        self._tracker.set_counter(key, confirmed=True, source="teste")
        return self._tracker.summary()

    def lab_report(self):
        rep = self._recorder.report(self._tracker.state["last_counters"], self._tracker.state["counter"])
        self._store.save("relatorio-rastreador.json", rep)
        return {"path": self._store.path("relatorio-rastreador.json"),
                "text": json.dumps(rep, ensure_ascii=False, indent=2)}

    def lab_export(self):
        rep = self._recorder.report(self._tracker.state["last_counters"], self._tracker.state["counter"])
        path = self._recorder.export_zip(rep)
        self.open_data_folder()
        return path

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
                          width=1240, height=820, min_size=(980, 660), background_color="#0A1A4F")
    webview.start()


if __name__ == "__main__":
    main()
