"""Rastreador de contadores: descobre quais números da conta contam baús.

Como funciona um teste:
1. No lobby, antes da partida, começa o teste: guarda uma foto de todos os contadores.
2. A pessoa joga e conta quantos baús abriu (total, raros e Sprite).
3. De volta ao lobby, termina o teste dizendo esses números.
4. O rastreador compara a foto de antes com a de agora e marca os contadores
   que subiram exatamente o número de baús informado.

Com alguns testes, o contador certo aparece batendo em todos. O relatório
não leva nada da conta além dos nomes e valores dos contadores.
"""
import json
import os
import re
import zipfile
from datetime import datetime

from tracker import BRT

LOG_LIMIT = 3000
KINDS = ("total", "raros", "sprite")


def _pattern(key):
    """Versão genérica da chave: troca números de temporada/semana por \\d+.

    Ajuda a reconhecer o mesmo contador em contas diferentes, quando a chave
    leva um número que muda (ex.: quest_s39_w2 -> quest_s\\d+_w\\d+).
    """
    return "^" + re.sub(r"\d+", r"\\d+", re.escape(key)) + "$"


class Recorder:
    def __init__(self, store, now):
        self.store = store
        self.now = now
        self.data = store.load("rastreador.json", {"log": [], "tests": [], "active": None})

    def _save(self):
        self.store.save("rastreador.json", self.data)

    # ---------- registro contínuo ----------
    def observe(self, before, after):
        """Guarda tudo o que mudou entre duas leituras da conta."""
        if not before:
            return
        changes = {k: [before.get(k), v] for k, v in after.items() if before.get(k) != v}
        if changes:
            self.data["log"].append({"ts": self.now(), "changes": changes})
            del self.data["log"][:-LOG_LIMIT]
            self._save()

    def recent(self, limit=40):
        out = []
        for entry in reversed(self.data["log"]):
            for k, (old, new) in entry["changes"].items():
                delta = (new or 0) - (old or 0) if isinstance(new, (int, float)) else None
                out.append({"ts": entry["ts"], "key": k, "old": old, "new": new, "delta": delta})
                if len(out) >= limit:
                    return out
        return out

    # ---------- cópias completas do perfil ----------
    def _snap_dir(self):
        d = self.store.path("rastreador")
        os.makedirs(d, exist_ok=True)
        return d

    def save_snapshot(self, test_id, moment, profiles):
        """Guarda o perfil inteiro (já sem a identificação da conta) para filtrar depois."""
        for name, data in profiles.items():
            if data is None:
                continue
            path = os.path.join(self._snap_dir(), f"{test_id}-{moment}-{name}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

    def export_zip(self, report):
        stamp = datetime.fromtimestamp(self.now(), BRT).strftime("%Y-%m-%d_%Hh%M")
        path = self.store.path(f"dados-rastreador_{stamp}.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("relatorio.json", json.dumps(report, ensure_ascii=False, indent=2))
            z.writestr("gravacoes.json", json.dumps(self.data, ensure_ascii=False))
            d = self._snap_dir()
            for name in sorted(os.listdir(d)):
                z.write(os.path.join(d, name), f"perfis/{name}")
        return path

    # ---------- testes ----------
    def start(self, counters, profiles=None):
        test_id = int(self.now())
        self.data["active"] = {"start": self.now(), "id": test_id, "baseline": dict(counters)}
        if profiles:
            self.save_snapshot(test_id, "antes", profiles)
        self._save()

    def cancel(self):
        self.data["active"] = None
        self._save()

    def finish(self, counters, declared, profiles=None):
        act = self.data["active"]
        if not act:
            raise ValueError("Nenhum teste em andamento.")
        if profiles:
            self.save_snapshot(act.get("id", int(act["start"])), "depois", profiles)
        base = act["baseline"]
        changes = {}
        for k, v in counters.items():
            old = base.get(k, 0)
            if isinstance(v, (int, float)) and v != old:
                # Contador que reiniciou no meio do teste: conta o valor novo inteiro.
                changes[k] = v - old if v >= old else v
        timeline = [e for e in self.data["log"] if e["ts"] >= act["start"]]
        test = {"id": act.get("id", int(act["start"])), "start": act["start"], "end": self.now(),
                "declared": {k: int(declared.get(k) or 0) for k in KINDS},
                "changes": changes, "timeline": timeline}
        self.data["tests"].append(test)
        self.data["active"] = None
        self._save()
        return self.describe(test)

    def describe(self, test):
        d = test["declared"]
        rows = []
        for k, delta in sorted(test["changes"].items(), key=lambda kv: -abs(kv[1])):
            match = [kind for kind in KINDS if d[kind] and delta == d[kind]]
            rows.append({"key": k, "delta": delta, "match": match})
        rows.sort(key=lambda r: (not r["match"], -abs(r["delta"])))
        return {"start": test["start"], "end": test["end"], "declared": d, "rows": rows,
                "counted": bool(d["total"])}

    def delete_test(self, index):
        tests = self.data["tests"]
        if 0 <= index < len(tests):
            tests.pop(index)
            self._save()

    def ranking(self):
        """Para cada tipo de baú, quantos testes cada contador acertou."""
        out = {}
        for kind in KINDS:
            tests = [t for t in self.data["tests"] if t["declared"].get(kind)]
            if not tests:
                continue
            score = {}
            for t in tests:
                want = t["declared"][kind]
                for k, delta in t["changes"].items():
                    s = score.setdefault(k, {"hits": 0, "moved": 0})
                    s["moved"] += 1
                    if delta == want:
                        s["hits"] += 1
            rows = [{"key": k, "hits": s["hits"], "moved": s["moved"], "tests": len(tests)}
                    for k, s in score.items() if s["hits"]]
            rows.sort(key=lambda r: (-r["hits"], r["moved"] - r["hits"], r["key"]))
            out[kind] = rows[:8]
        return out

    def state(self):
        act = self.data["active"]
        reads = sum(1 for e in self.data["log"] if act and e["ts"] >= act["start"])
        return {
            "active": act and {"start": act["start"], "changes": reads},
            "tests": [self.describe(t) for t in self.data["tests"]][::-1],
            "ranking": self.ranking(),
            "recent": self.recent(),
        }

    def report(self, counters, chosen):
        """Relatório para mandar ao desenvolvedor. Sem token, e-mail ou ID da conta."""
        ranking = self.ranking()
        best = {kind: rows[0] for kind, rows in ranking.items()
                if rows and rows[0]["hits"] == rows[0]["tests"]}
        return {
            "gerado_em": datetime.fromtimestamp(self.now(), BRT).isoformat(timespec="minutes"),
            "testes": len(self.data["tests"]),
            "sugestao_padrao": {kind: {"chave": r["key"], "padrao": _pattern(r["key"]),
                                       "acertos": f'{r["hits"]}/{r["tests"]}'} for kind, r in best.items()},
            "ranking": ranking,
            "contador_em_uso": chosen and {"chave": chosen["key"], "conferido": chosen.get("confirmed")},
            "testes_detalhe": [{**self.describe(t), "linha_do_tempo": [
                {"hora": datetime.fromtimestamp(e["ts"], BRT).strftime("%H:%M:%S"), "mudou": e["changes"]}
                for e in t.get("timeline", [])]} for t in self.data["tests"]],
            "contadores_com_bau_no_nome": {k: v for k, v in counters.items()
                                           if any(w in k.lower() for w in ("chest", "treasure", "sprite", "loot"))},
        }
