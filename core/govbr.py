"""
Integração com o Login Único (Entrar com gov.br).
Documentação oficial: https://acesso.gov.br/roteiro-tecnico/iniciarintegracao.html

Fluxo: Authorization Code + PKCE (S256).
Ambiente controlado por GOVBR_ENV ("staging" ou "production") nas variáveis de ambiente.
"""

import base64
import hashlib
import os
import secrets

import requests

ENV = os.environ.get("GOVBR_ENV", "staging")

BASE_URL = (
    "https://sso.acesso.gov.br"
    if ENV == "production"
    else "https://sso.staging.acesso.gov.br"
)

AUTHORIZE_URL = f"{BASE_URL}/authorize"
TOKEN_URL = f"{BASE_URL}/token"
USERINFO_URL = f"{BASE_URL}/userinfo/"
LOGOUT_URL = f"{BASE_URL}/logout"

CLIENT_ID = os.environ.get("GOVBR_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOVBR_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("GOVBR_REDIRECT_URI", "")

SCOPE = "openid+email+profile"


def is_configured():
    return bool(CLIENT_ID and CLIENT_SECRET and REDIRECT_URI)


def _gerar_pkce_pair():
    verifier = secrets.token_urlsafe(64)[:96]  # 43-128 chars exigido
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def montar_url_autorizacao(request):
    """Gera a URL de redirecionamento para o gov.br e guarda state/nonce/verifier na sessão."""
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(16)
    code_verifier, code_challenge = _gerar_pkce_pair()

    request.session["govbr_state"] = state
    request.session["govbr_nonce"] = nonce
    request.session["govbr_code_verifier"] = code_verifier

    params = (
        f"response_type=code&client_id={CLIENT_ID}&scope={SCOPE}"
        f"&redirect_uri={REDIRECT_URI}&nonce={nonce}&state={state}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256"
    )
    return f"{AUTHORIZE_URL}?{params}"


def trocar_code_por_token(code, code_verifier):
    """Passo 6 do roteiro: troca o code por access_token/id_token."""
    credenciais = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {credenciais}",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }
    resp = requests.post(TOKEN_URL, headers=headers, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def obter_userinfo(access_token):
    """Passo 9 (alternativa): consulta os dados básicos do cidadão autenticado."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(USERINFO_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def montar_url_logout(post_logout_redirect_uri):
    return f"{LOGOUT_URL}?post_logout_redirect_uri={post_logout_redirect_uri}"
