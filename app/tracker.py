"""Transforma o perfil da Epic em contadores e guarda o histórico no PC.

Ainda não sabemos o nome exato do contador de baús do Treasure Hunters.
Por isso a ferramenta lista todos os contadores numéricos do perfil e você
marca qual (ou quais) contam baús. O total é somado a partir daí.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))  # Brasília não tem horário de verão desde 2019

# Palavras que costumam aparecer nos contadores e itens do evento.
KEYWORDS = ("chest", "treasure", "pirate", "token", "shopaccess", "captain",
            "fragment", "map", "onepiece", "sprite", "buried", "bau")

COSMETIC_PREFIXES = ("Athena", "Cosmetic", "Sparks", "Vehicle", "Juno")
NOT_DROPS = ("Quest:", "ChallengeBundle", "ChallengeBundleSchedule:")


def extract_counters(profile):
    """Retorna {chave: valor} com todo número que pode ser um contador."""
    counters = {}
    for item in (profile.get("items") or {}).values():
        tid = item.get("templateId", "")
        attrs = item.get("attributes") or {}
        for k, v in attrs.items():
            if k.startswith("completion_") and isinstance(v, (int, float)) and not isinstance(v, bool):
                counters[f"{tid}/{k}"] = v
        qty = item.get("quantity")
        if not tid.startswith(COSMETIC_PREFIXES) and isinstance(qty, (int, float)) and qty != 1:
            counters[f"{tid}#quantidade"] = qty
    stats = ((profile.get("stats") or {}).get("attributes")) or {}
    for k, v in stats.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            counters[f"stats/{k}"] = v
    return counters


def extract_items(profile):
    """Retorna {templateId: quantidade} de tudo o que está na conta."""
    out = {}
    for item in (profile.get("items") or {}).values():
        tid = item.get("templateId")
        if tid:
            out[tid] = out.get(tid, 0) + int(item.get("quantity") or 1)
    return out


def matches_keywords(text):
    low = text.lower()
    return any(k in low for k in KEYWORDS)


def looks_like_token(template_id):
    low = template_id.lower().replace("_", "")
    return "pirate" in low and ("token" in low or "shop" in low or "access" in low)


class Store:
    """Arquivos em %APPDATA%\\CacaAoToken (ou ~/.caca-ao-token fora do Windows)."""

    def __init__(self, folder=None):
        if folder is None:
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            folder = os.path.join(base, "CacaAoToken" if os.environ.get("APPDATA") else ".caca-ao-token")
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def path(self, name):
        return os.path.join(self.folder, name)

    def load(self, name, default):
        try:
            with open(self.path(name), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def save(self, name, data):
        tmp = self.path(name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path(name))

    def delete(self, name):
        try:
            os.remove(self.path(name))
        except FileNotFoundError:
            pass


class Tracker:
    def __init__(self, store, now=time.time):
        self.store = store
        self.now = now
        self.state = store.load("estado.json", {
            "selected": {},      # chave -> {"total": n, "last": valor bruto}
            "last_counters": {},
            "last_items": None,
            "events": [],        # [{"ts", "baus"}] cada aumento no total
            "drops": [],         # [{"ts", "templateId", "bau"}]
            "manual_prizes": [], # nomes marcados à mão
            "first_seen": None,
        })
        self.session_start = self.now()
        self.session_gained = 0
        self.prev_counters = dict(self.state["last_counters"])

    # ---------- atualização ----------
    def update(self, profile):
        counters = extract_counters(profile)
        items = extract_items(profile)
        ts = self.now()
        st = self.state
        if st["first_seen"] is None:
            st["first_seen"] = ts

        gained = 0
        for key, sel in st["selected"].items():
            if key not in counters:
                continue
            new, old = counters[key], sel["last"]
            # Se o valor caiu, o contador reiniciou (quest semanal): conta do zero.
            delta = new - old if new >= old else new
            if delta > 0:
                sel["total"] += delta
                gained += delta
            sel["last"] = new
        self.session_gained += gained
        if gained:
            st["events"].append({"ts": ts, "baus": gained})

        new_items = []
        if st["last_items"] is not None:
            for tid in items:
                if tid not in st["last_items"] and not tid.startswith(NOT_DROPS):
                    new_items.append(tid)
                    st["drops"].append({"ts": ts, "templateId": tid, "bau": self.total()})

        self.prev_counters = st["last_counters"]
        st["last_counters"] = counters
        st["last_items"] = items
        st["last_refresh"] = ts
        self.store.save("estado.json", st)
        return {"gained": gained, "new_items": new_items,
                "token": [t for t in new_items if looks_like_token(t)]}

    # ---------- escolha do contador ----------
    def set_selected(self, key, on):
        sel = self.state["selected"]
        if on and key not in sel:
            value = self.state["last_counters"].get(key, 0)
            # O valor atual já entra no total: são baús abertos antes da ferramenta.
            sel[key] = {"total": value, "last": value}
        elif not on:
            sel.pop(key, None)
        self.store.save("estado.json", self.state)

    def toggle_manual_prize(self, name):
        lst = self.state["manual_prizes"]
        if name in lst:
            lst.remove(name)
        else:
            lst.append(name)
        self.store.save("estado.json", self.state)
        return name in lst

    # ---------- leitura ----------
    def total(self):
        return sum(s["total"] for s in self.state["selected"].values())

    def summary(self):
        ts = self.now()
        today = datetime.fromtimestamp(ts, BRT).date()
        today_count = sum(e["baus"] for e in self.state["events"]
                          if datetime.fromtimestamp(e["ts"], BRT).date() == today)
        session = self.session_gained
        hours = (ts - self.session_start) / 3600
        return {
            "total": self.total(),
            "today": today_count,
            "session": session,
            # Ritmo só depois de 10 minutos, senão o número sai absurdo.
            "rate": round(session / hours, 1) if hours >= 1 / 6 else None,
            "has_counter": bool(self.state["selected"]),
            "last_refresh": self.state.get("last_refresh"),
            "per_day": self.per_day(),
        }

    def per_day(self):
        days = {}
        for e in self.state["events"]:
            d = datetime.fromtimestamp(e["ts"], BRT).strftime("%Y-%m-%d")
            days[d] = days.get(d, 0) + e["baus"]
        return [{"day": d, "baus": n} for d, n in sorted(days.items())]

    def counters_view(self):
        cur = self.state["last_counters"]
        prev = self.prev_counters
        rows = []
        for key, value in cur.items():
            rows.append({
                "key": key,
                "value": value,
                "delta": value - prev[key] if key in prev else None,
                "selected": key in self.state["selected"],
                "hint": matches_keywords(key),
            })
        rows.sort(key=lambda r: (not r["selected"], not (r["delta"] or 0), not r["hint"], r["key"]))
        return rows

    def diagnostics(self):
        counters = self.state["last_counters"]
        items = self.state["last_items"] or {}
        return {
            "gerado_em": datetime.fromtimestamp(self.now(), BRT).isoformat(),
            "contadores_suspeitos": {k: v for k, v in counters.items() if matches_keywords(k)},
            "contadores_escolhidos": list(self.state["selected"]),
            "itens_suspeitos": {k: v for k, v in items.items()
                                if matches_keywords(k) and not k.startswith(COSMETIC_PREFIXES)},
            "drops": self.state["drops"][-50:],
            "total_contadores": len(counters),
            "total_itens": len(items),
        }
