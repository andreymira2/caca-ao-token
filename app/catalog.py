"""Nomes dos itens (o perfil da Epic só tem códigos como AthenaCharacter:cid_123).

Usa o fortnite-api.com, um site público da comunidade, e guarda o resultado.
"""
import json
import urllib.parse
import urllib.request

API = "https://fortnite-api.com/v2/cosmetics/br/"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CacaAoToken/0.1"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


class Catalog:
    def __init__(self, store):
        self.store = store
        self.names = store.load("nomes.json", {})

    def name(self, template_id):
        """Nome em inglês do item, ou None se não achar."""
        if template_id in self.names:
            return self.names[template_id]
        cid = template_id.split(":", 1)[-1]
        name = None
        try:
            data = _get(API + urllib.parse.quote(cid))
            name = (data.get("data") or {}).get("name")
        except Exception:
            return None  # sem internet ou item fora do catálogo: tenta de novo depois
        self.names[template_id] = name
        self.store.save("nomes.json", self.names)
        return name


def same_name(a, b):
    norm = lambda s: "".join(ch for ch in (s or "").lower() if ch.isalnum())
    return bool(a and b) and norm(a) == norm(b)
