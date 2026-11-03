"""Entra ID (OIDC). Mesmo padrão de clients/: o app fala com o EntraGateway; a implementação
decide como. EntraHttpx fala com o Entra de verdade (ou com o mock em localhost:8001).

Só o fluxo Authorization Code + PKCE, com o backend como client confidencial."""

import asyncio
import base64
import hashlib
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

from crm.shared.config import Settings


class FalhaDeAutenticacao(Exception):
    """Code/refresh recusado ou id_token inválido. Vira 401 no router."""


@dataclass(frozen=True)
class Tokens:
    id_token: str
    refresh_token: str | None
    expires_in: int


class EntraGateway(Protocol):
    def url_login(self, state: str, nonce: str, code_verifier: str) -> str: ...

    async def trocar_code(self, code: str, code_verifier: str) -> Tokens: ...

    async def renovar(self, refresh_token: str) -> Tokens: ...

    async def validar_id_token(self, id_token: str, nonce: str | None) -> dict[str, Any]: ...

    def url_logout(self, voltar_para: str) -> str: ...


def desafio_pkce(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class EntraHttpx(EntraGateway):
    """Um por processo (guarda o discovery e o cache de chaves)."""

    def __init__(self, settings: Settings):
        self.s = settings
        self._base = f"{settings.auth_url}/{settings.auth_tenant}"
        self._discovery: dict[str, Any] | None = None
        self._jwks: PyJWKClient | None = None

    # --- URLs ---------------------------------------------------------------
    def url_login(self, state: str, nonce: str, code_verifier: str) -> str:
        query = urlencode(
            {
                "client_id": self.s.auth_client_id,
                "response_type": "code",
                "redirect_uri": self.s.auth_redirect_uri,
                "scope": self.s.auth_scope,
                "state": state,
                "nonce": nonce,
                "code_challenge": desafio_pkce(code_verifier),
                "code_challenge_method": "S256",
            }
        )
        return f"{self._base}/oauth2/v2.0/authorize?{query}"

    def url_logout(self, voltar_para: str) -> str:
        return f"{self._base}/oauth2/v2.0/logout?{urlencode({'post_logout_redirect_uri': voltar_para})}"

    # --- Token endpoint -----------------------------------------------------
    async def trocar_code(self, code: str, code_verifier: str) -> Tokens:
        return await self._token(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.s.auth_redirect_uri,
                "code_verifier": code_verifier,
            }
        )

    async def renovar(self, refresh_token: str) -> Tokens:
        return await self._token(
            {"grant_type": "refresh_token", "refresh_token": refresh_token, "scope": self.s.auth_scope}
        )

    async def _token(self, form: dict[str, str]) -> Tokens:
        form = {
            **form,
            "client_id": self.s.auth_client_id,
            "client_secret": self.s.auth_client_secret,
        }
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.post(f"{self._base}/oauth2/v2.0/token", data=form)
        if resp.status_code != 200:
            raise FalhaDeAutenticacao(resp.json().get("error_description", "token recusado"))
        body = resp.json()
        if "id_token" not in body:
            raise FalhaDeAutenticacao("resposta sem id_token (scope openid?)")
        return Tokens(
            id_token=body["id_token"],
            refresh_token=body.get("refresh_token"),
            expires_in=int(body.get("expires_in", 3600)),
        )

    # --- Validação do id_token ----------------------------------------------
    async def validar_id_token(self, id_token: str, nonce: str | None) -> dict[str, Any]:
        discovery = await self._carregar_discovery()
        try:
            chave = await asyncio.to_thread(self._jwks_client.get_signing_key_from_jwt, id_token)
            claims = jwt.decode(
                id_token,
                chave.key,
                algorithms=["RS256"],
                audience=self.s.auth_client_id,
                issuer=discovery["issuer"],
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise FalhaDeAutenticacao(f"id_token inválido: {exc}") from exc
        if claims.get("tid") != self.s.auth_tenant:
            raise FalhaDeAutenticacao("id_token de outro tenant")
        # nonce só vem no id_token do login; no refresh o Entra não o repete
        if nonce is not None and claims.get("nonce") != nonce:
            raise FalhaDeAutenticacao("nonce não confere")
        return claims

    async def _carregar_discovery(self) -> dict[str, Any]:
        if self._discovery is None:
            url = f"{self._base}/v2.0/.well-known/openid-configuration"
            async with httpx.AsyncClient(timeout=10) as http:
                resp = await http.get(url)
                resp.raise_for_status()
            self._discovery = resp.json()
            self._jwks = PyJWKClient(self._discovery["jwks_uri"], cache_keys=True)
        return self._discovery

    @property
    def _jwks_client(self) -> PyJWKClient:
        assert self._jwks is not None  # sempre depois de _carregar_discovery()
        return self._jwks
