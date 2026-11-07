"""Conversa com os servidores da Epic: login e leitura do perfil do Fortnite.

Usa só a biblioteca padrão do Python, para o .exe ficar pequeno.
"""
import base64
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

# Cliente público do Fortnite para Android. É o mesmo que ferramentas da
# comunidade usam para "login de dispositivo" (lembrar o login sem senha).
CLIENT_ID = "3f69e56c7649492c8cc29f1af08a8a12"
CLIENT_SECRET = "b51ee9cb12234f50a69efa67ef53812e"

ACCOUNT_API = "https://account-public-service-prod.ol.epicgames.com/account/api"
FORTNITE_API = "https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api"

_REDIRECT = f"https://www.epicgames.com/id/api/redirect?clientId={CLIENT_ID}&responseType=code"
LOGIN_URL = "https://www.epicgames.com/id/login?redirectUrl=" + urllib.parse.quote(_REDIRECT, safe="")

USER_AGENT = "CacaAoToken/0.1"


class EpicError(Exception):
    def __init__(self, message, code=None, status=None):
        super().__init__(message)
        self.code = code
        self.status = status


def _request(method, url, *, token=None, basic=False, form=None, body=None, timeout=20):
    headers = {"User-Agent": USER_AGENT}
    data = None
    if basic:
        raw = f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
        headers["Authorization"] = "basic " + base64.b64encode(raw).decode()
    elif token:
        headers["Authorization"] = "bearer " + token
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        try:
            info = json.loads(e.read().decode("utf-8"))
        except Exception:
            info = {}
        raise EpicError(
            info.get("errorMessage") or f"Erro {e.code} da Epic",
            code=info.get("errorCode"),
            status=e.code,
        ) from None
    except urllib.error.URLError as e:
        raise EpicError(f"Sem conexão com a Epic ({e.reason})") from None


def extract_code(text):
    """Aceita o código puro ou o JSON inteiro que a página da Epic mostra."""
    text = (text or "").strip()
    m = re.search(r'"authorizationCode"\s*:\s*"([0-9a-f]{32})"', text)
    if m:
        return m.group(1)
    m = re.fullmatch(r'"?([0-9a-f]{32})"?', text)
    return m.group(1) if m else None


def token_from_code(code):
    return _request("POST", ACCOUNT_API + "/oauth/token", basic=True,
                    form={"grant_type": "authorization_code", "code": code})


def token_from_device(device):
    return _request("POST", ACCOUNT_API + "/oauth/token", basic=True, form={
        "grant_type": "device_auth",
        "account_id": device["accountId"],
        "device_id": device["deviceId"],
        "secret": device["secret"],
    })


def create_device_auth(token):
    res = _request("POST", f"{ACCOUNT_API}/public/account/{token['account_id']}/deviceAuth",
                   token=token["access_token"], body={})
    return {"accountId": res["accountId"], "deviceId": res["deviceId"], "secret": res["secret"]}


def delete_device_auth(token, device):
    _request("DELETE", f"{ACCOUNT_API}/public/account/{device['accountId']}/deviceAuth/{device['deviceId']}",
             token=token["access_token"])


def query_profile(token, profile_id="athena"):
    url = (f"{FORTNITE_API}/game/v2/profile/{token['account_id']}/client/QueryProfile"
           f"?profileId={profile_id}&rvn=-1")
    res = _request("POST", url, token=token["access_token"], body={})
    return res["profileChanges"][0]["profile"]


class Session:
    """Guarda o token de acesso e renova sozinho quando ele vence."""

    def __init__(self, device):
        self.device = device
        self.token = None
        self.expires_at = 0

    def access(self):
        if not self.token or time.time() > self.expires_at - 120:
            self.token = token_from_device(self.device)
            self.expires_at = time.time() + int(self.token.get("expires_in", 7200))
        return self.token

    @property
    def display_name(self):
        return (self.token or {}).get("displayName")
