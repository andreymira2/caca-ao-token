"""Transforma o perfil da Epic em contadores e guarda o histórico no PC.

Ainda não sabemos o nome exato do contador de baús do Treasure Hunters.
Por isso a ferramenta lista todos os contadores numéricos do perfil e você
marca qual (ou quais) contam baús. O total é somado a partir daí.
"""
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))  # Brasília não tem horário de verão desde 2019

# Palavras que costumam aparecer nos contadores e itens do evento.
KEYWORDS = ("chest", "treasure", "pirate", "token", "shopaccess", "captain",
            "fragment", "map", "onepiece", "sprite", "buried", "bau")

# Palavras que indicam um contador de baús dentro das missões do evento.
CHEST_WORDS = ("chest", "treasure", "sprite", "bau", "loot")
QUEST_PREFIXES = ("Quest:", "ChallengeBundle")

# Trilhas de baús do Treasure Hunters, descobertas com o Rastreador (perfil real, temporada 43).
# Cada trilha tem várias missões (metas 25/100/250/500/1000 no total); o número é
# acumulado entre as metas, então o maior valor entre elas é o total atual.
# Quando a última meta é resgatada, o jogo para de contar.
EVENT_TRACKS = {
    "total": r"Quest:quest_s\d+_treasurehunt_count_\d+/completion_quest_s\d+_treasurehunt_count_\d+_obj0",
    "raros": r"Quest:quest_s\d+_treasurehunt_rarity_\d+/completion_quest_s\d+_treasurehunt_rarity_\d+_obj0",
    "sprite": r"Quest:quest_s\d+_treasurehunt_sprites_\d+/completion_quest_s\d+_treasurehunt_sprites_\d+_obj0",
}
EVENT_KEY = "evento/{}"


def event_tracks(profile, patterns=EVENT_TRACKS):
    """Valor atual de cada trilha e se ela já chegou na última meta."""
    found = {}
    for item in (profile.get("items") or {}).values():
        tid = item.get("templateId", "")
        attrs = item.get("attributes") or {}
        for attr, value in attrs.items():
            if not attr.startswith("completion_") or not isinstance(value, (int, float)):
                continue
            key = f"{tid}/{attr}"
            for kind, pat in patterns.items():
                if re.fullmatch(pat, key):
                    t = found.setdefault(kind, {"value": 0, "quests": 0, "open": 0})
                    t["value"] = max(t["value"], value)
                    t["quests"] += 1
                    if attrs.get("quest_state") != "Claimed":
                        t["open"] += 1
    for t in found.values():
        t["capped"] = t["open"] == 0  # todas as metas resgatadas: o jogo parou de contar
        del t["open"]
    return found


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
            "counter": None,     # {"key", "total", "last", "confirmed", "game_value", "confirmed_at"}
            "last_counters": {},
            "last_items": None,
            "events": [],        # [{"ts", "baus"}] cada aumento no total
            "drops": [],         # [{"ts", "templateId", "bau"}]
            "manual_prizes": [], # nomes marcados à mão
            "first_seen": None,
        })
        # Versões antigas somavam vários contadores, o que inflava o total. Recomeça.
        if "selected" in self.state:
            self.state.pop("selected")
            self.state.setdefault("counter", None)
        self.presets = [r"evento/total"]  # contadores confirmados; o evento.json pode trocar
        self.tracks = dict(EVENT_TRACKS)
        self.session_start = self.now()
        self.session_gained = 0
        self.prev_counters = dict(self.state["last_counters"])

    # ---------- atualização ----------
    def update(self, profile):
        counters = extract_counters(profile)
        tracks = event_tracks(profile, self.tracks)
        for kind, t in tracks.items():
            counters[EVENT_KEY.format(kind)] = t["value"]
        self.state["evento"] = tracks
        items = extract_items(profile)
        ts = self.now()
        st = self.state
        if st["first_seen"] is None:
            st["first_seen"] = ts

        gained = 0
        c = st["counter"]
        if c and c["key"] in counters:
            new, old = counters[c["key"]], c["last"]
            # Se o valor caiu, o contador reiniciou: conta do zero.
            delta = new - old if new >= old else new
            if delta > 0:
                c["total"] += delta
                gained = delta
            c["last"] = new
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
        c = st["counter"]
        # A trilha oficial do evento vence qualquer palpite antigo ainda não conferido.
        if c is None or (not c.get("confirmed") and c.get("source") != "padrao") or \
                (c.get("source") == "padrao" and c["key"] != self.preset_key()):
            preset = self.preset_key()
            if preset:
                self._use(preset, confirmed=True, source="padrao")
            elif c is None:
                best = self.chest_candidates()
                if best:
                    self._use(best[0]["key"], confirmed=False)
        self.store.save("estado.json", st)
        return {"gained": gained, "new_items": new_items,
                "token": [t for t in new_items if looks_like_token(t)]}

    # ---------- escolha do contador ----------
    def chest_candidates(self):
        """Contadores de missão que parecem contar baús, do mais provável ao menos."""
        rows = []
        for key, value in self.state["last_counters"].items():
            if not key.startswith(QUEST_PREFIXES):
                continue
            low = key.lower()
            score = sum(w in low for w in CHEST_WORDS) + (2 if "chest" in low else 0)
            if score:
                rows.append({"key": key, "value": value, "score": score})
        rows.sort(key=lambda r: (-r["score"], -r["value"]))
        return rows

    def find_by_value(self, n):
        """Contadores de missão com exatamente o número que o jogo mostra."""
        hits = [{"key": k, "value": v, "chest": any(w in k.lower() for w in CHEST_WORDS)}
                for k, v in self.state["last_counters"].items()
                if k.startswith(QUEST_PREFIXES) and v == n]
        hits.sort(key=lambda r: not r["chest"])
        return hits

    def preset_key(self):
        """Primeiro contador da conta que bate com um padrão confirmado."""
        for pat in self.presets:
            rx = re.compile(pat)
            hit = next((k for k in self.state["last_counters"] if rx.fullmatch(k)), None)
            if hit:
                return hit
        return None

    def _use(self, key, confirmed, source="manual"):
        value = self.state["last_counters"].get(key, 0)
        # O contador do jogo já é o total do evento: o valor atual entra inteiro.
        self.state["counter"] = {"key": key, "total": value, "last": value, "source": source,
                                 "confirmed": confirmed, "game_value": value if confirmed else None,
                                 "confirmed_at": self.now() if confirmed else None}

    def set_counter(self, key, confirmed=True, source="manual"):
        # Fora das missões, só aceita a trilha do evento ou um contador que passou num teste.
        if not key.startswith(QUEST_PREFIXES + ("evento/",)) and source != "teste":
            raise ValueError("Só contadores de missão podem contar baús.")
        self._use(key, confirmed, source)
        self.store.save("estado.json", self.state)

    def confirm_counter(self):
        c = self.state["counter"]
        if c:
            c.update(confirmed=True, game_value=c["last"], confirmed_at=self.now())
            self.store.save("estado.json", self.state)

    def reset_counter(self):
        self.state["counter"] = None
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
        c = self.state["counter"]
        return c["total"] if c else 0

    def summary(self):
        ts = self.now()
        today = datetime.fromtimestamp(ts, BRT).date()
        today_count = sum(e["baus"] for e in self.state["events"]
                          if datetime.fromtimestamp(e["ts"], BRT).date() == today)
        session = self.session_gained
        hours = (ts - self.session_start) / 3600
        rate = round(session / hours, 1) if hours >= 1 / 6 else None
        if rate is None:
            # Sessão curta: usa o ritmo de hoje, do primeiro ao último baú contado.
            today_ts = [e["ts"] for e in self.state["events"]
                        if datetime.fromtimestamp(e["ts"], BRT).date() == today]
            span = (max(today_ts) - min(today_ts)) / 3600 if today_ts else 0
            if span >= 1 / 6:
                rate = round(today_count / span, 1)
        return {
            "total": self.total(),
            "today": today_count,
            "session": session,
            # Ritmo só com 10 minutos de dados, senão o número sai absurdo.
            "rate": rate,
            "has_counter": bool(self.state["counter"]),
            "counter": self.state["counter"],
            "has_data": bool(self.state["last_counters"]),
            "evento": self.state.get("evento") or {},
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
                "selected": key == (self.state["counter"] or {}).get("key"),
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
            "contador_escolhido": self.state["counter"],
            "itens_suspeitos": {k: v for k, v in items.items()
                                if matches_keywords(k) and not k.startswith(COSMETIC_PREFIXES)},
            "drops": self.state["drops"][-50:],
            "total_contadores": len(counters),
            "total_itens": len(items),
        }
