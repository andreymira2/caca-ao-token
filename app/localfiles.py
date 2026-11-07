"""Arquivos que o próprio Fortnite grava no PC: o log e os replays.

O perfil da Epic para de contar baús depois da última meta do evento. Estes
arquivos ficam no computador e talvez registrem cada baú aberto. Aqui só
recolhemos o trecho das partidas gravadas no Rastreador, sem dados pessoais,
para descobrir se dá para contar a partir deles.
"""
import glob
import os
import re
from datetime import datetime, timezone

# Linhas do log começam com a hora em UTC: [2026.11.07-15.43.24:123]
LOG_TS = re.compile(r"^\[(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2}):\d{3}\]")
MARGIN = 120  # segundos antes e depois de cada gravação

REDACT = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "<email>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b"), "<ip>"),
    (re.compile(r"\b[0-9a-fA-F]{32}\b"), "<id>"),
    (re.compile(r"(?i)(bearer|token|auth|ticket|password|secret)([\"'=: ]+)\S+"), r"\1\2<oculto>"),
    (re.compile(r"eg1~[\w.~-]+"), "<oculto>"),
]


def saved_dir():
    base = os.environ.get("LOCALAPPDATA")
    return os.path.join(base, "FortniteGame", "Saved") if base else None


def _line_time(line):
    m = LOG_TS.match(line)
    if not m:
        return None
    y, mo, d, h, mi, s = map(int, m.groups())
    return datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc).timestamp()


def redact(text, secrets=()):
    for s in secrets:
        if s:
            text = text.replace(s, "<conta>")
    for rx, sub in REDACT:
        text = rx.sub(sub, text)
    return text


def log_excerpt(windows, secrets=(), folder=None):
    """Linhas dos logs do Fortnite dentro das janelas (início, fim) das gravações."""
    folder = folder or saved_dir()
    if not folder:
        return None
    files = sorted(glob.glob(os.path.join(folder, "Logs", "FortniteGame*.log")), key=os.path.getmtime)
    if not files:
        return None
    out = []
    for path in files[-4:]:  # o log atual e os últimos backups
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                current = None
                for line in f:
                    t = _line_time(line)
                    if t is not None:
                        current = t
                    if current is not None and any(a - MARGIN <= current <= b + MARGIN for a, b in windows):
                        out.append(line)
        except OSError:
            continue
    return redact("".join(out), secrets) if out else ""


def replays(windows, folder=None):
    """Replays gravados durante as gravações do Rastreador."""
    folder = folder or saved_dir()
    if not folder:
        return []
    hits = []
    for path in glob.glob(os.path.join(folder, "Demos", "*.replay")):
        t = os.path.getmtime(path)
        if any(a - MARGIN <= t <= b + 15 * 60 for a, b in windows):
            hits.append(path)
    return sorted(hits, key=os.path.getmtime)[-3:]
