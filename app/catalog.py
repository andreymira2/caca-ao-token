"""Nome, imagem e raridade dos itens (o perfil da Epic só tem códigos).

Usa o fortnite-api.com, que publica as artes oficiais dos itens, e guarda o
resultado no PC. Sem internet, os itens aparecem sem imagem.
"""
import json
import time
import urllib.parse
import urllib.request

API = "https://fortnite-api.com/v2/cosmetics"
RETRY_MISS = 6 * 3600  # item não encontrado: tenta de novo depois de 6 horas


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CacaAoToken/0.2"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _norm(s):
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def same_name(a, b):
    return bool(a and b) and _norm(a) == _norm(b)


def _from_br(x):
    imgs = x.get("images") or {}
    return {"id": x.get("id"), "name": x.get("name"),
            "image": imgs.get("icon") or imgs.get("smallIcon") or imgs.get("featured"),
            "rarity": (x.get("rarity") or {}).get("value")}


def _from_car(x):
    imgs = x.get("images") or {}
    return {"id": x.get("id"), "name": x.get("name"), "image": imgs.get("large") or imgs.get("small"),
            "rarity": (x.get("rarity") or {}).get("value")}


def _from_track(x):
    return {"id": x.get("id"), "name": x.get("title"), "image": x.get("albumArt"), "rarity": "rare"}


class Catalog:
    def __init__(self, store, fetch=_get):
        self.store = store
        self.fetch = fetch
        self.cache = store.load("catalogo.json", {})
        self._lists = {}

    def _save(self, key, info):
        self.cache[key] = {**(info or {}), "found": bool(info), "at": time.time()}
        self.store.save("catalogo.json", self.cache)
        return info

    def _cached(self, key):
        c = self.cache.get(key)
        if c is None:
            return False, None
        if c.get("found"):
            return True, c
        return time.time() - c.get("at", 0) < RETRY_MISS, None

    def _list(self, kind):
        if kind not in self._lists:
            self._lists[kind] = self.fetch(f"{API}/{kind}").get("data") or []
        return self._lists[kind]

    def item(self, template_id):
        """Informação de um item da conta, pelo código (ex.: AthenaCharacter:cid_123)."""
        key = "id:" + template_id.split(":", 1)[-1].lower()
        hit, info = self._cached(key)
        if hit:
            return info
        try:
            return self._save(key, self._lookup_id(template_id.split(":", 1)[-1]))
        except Exception:
            return None  # sem internet: tenta de novo na próxima vez

    def _lookup_id(self, cid):
        low = cid.lower()
        for x in self._list("cars"):
            if (x.get("id") or "").lower() == low:
                return _from_car(x)
        for x in self._list("tracks"):
            if (x.get("id") or "").lower() == low:
                return _from_track(x)
        try:
            data = self.fetch(f"{API}/br/{urllib.parse.quote(cid)}").get("data")
        except Exception:
            data = None
        return _from_br(data) if data else None

    def prize(self, prize):
        """Informação de um prêmio do evento.json (pelo campo 'id' ou pelo nome)."""
        if prize.get("id"):
            return self.item(prize["id"])
        key = "nome:" + _norm(prize.get("nome"))
        hit, info = self._cached(key)
        if hit:
            return info
        try:
            return self._save(key, self._lookup_name(prize["nome"], prize.get("tipo", "")))
        except Exception:
            return None

    def _lookup_name(self, name, kind):
        kind = kind.lower()
        if kind == "carro":
            x = next((x for x in self._list("cars") if same_name(x.get("name"), name)), None)
            return _from_car(x) if x else None
        if kind == "jam track":
            x = next((x for x in self._list("tracks") if same_name(x.get("title"), name)), None)
            return _from_track(x) if x else None
        try:
            data = self.fetch(f"{API}/br/search?name={urllib.parse.quote(name)}&matchMethod=full").get("data")
        except Exception:
            data = None
        return _from_br(data) if data else None
