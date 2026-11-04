"""Infra comum a todos os gateways do Core: autenticação, chave de DI do client HTTP e a base
com o contexto da chamada.

`organization` (Settings) e `branch` (agência do usuário) são contexto de toda chamada ao Core
e preenchidos aqui."""

import time
from collections.abc import AsyncGenerator
from typing import Any, NewType

import httpx

from crm.shared.auth import UsuarioAtual
from crm.shared.config import Settings
from crm.shared.errors import RegraDeNegocio

CoreHttp = NewType(
    "CoreHttp", httpx.AsyncClient
)  # chave de DI: distingue de outros AsyncClient


class CoreAuth(httpx.Auth):
    """OAuth client_credentials: busca o token no 1º uso, renova ao expirar ou num 401.
    Vive dentro do client (um por processo), então o token é compartilhado."""

    requires_response_body = True

    def __init__(self, base_url: str, key: str, secret: str):
        self._url = f"{base_url.rstrip('/')}/oauth/token"
        self._form = {
            "grant_type": "client_credentials",
            "client_id": key,
            "client_secret": secret,
        }
        self._token: str | None = None
        self._expira = 0.0  # time.monotonic()

    def _pedido_token(self) -> httpx.Request:
        return httpx.Request("POST", self._url, data=self._form)

    async def _guardar(self, resp: httpx.Response) -> None:
        # o httpx entrega a resposta ao fluxo ainda sem ler o corpo (requires_response_body
        # só vale para o async_auth_flow padrão, que aqui é sobrescrito)
        await resp.aread()
        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        self._expira = time.monotonic() + int(body.get("expires_in", 300)) - 30

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        if self._token is None or self._expira <= time.monotonic():
            await self._guardar((yield self._pedido_token()))
        request.headers["Authorization"] = f"Bearer {self._token}"
        resp = yield request
        if resp.status_code == 401:  # token revogado antes de expirar
            await self._guardar((yield self._pedido_token()))
            request.headers["Authorization"] = f"Bearer {self._token}"
            yield request


class CoreHttpxBase:
    """Base dos gateways HTTP do Core. Um por requisição: carrega o usuário (agência =
    `branch`). O client HTTP (base_url e autenticação) vem pronto do container."""

    def __init__(self, http: CoreHttp, settings: Settings, usuario: UsuarioAtual):
        self.http = http
        self.s = settings
        self.usuario = usuario

    def _filtro(self) -> dict[str, str]:
        if not self.usuario.agencia:
            raise RegraDeNegocio("Usuário sem agência: não dá para chamar o Core")
        return {"organization": self.s.api_organization, "branch": self.usuario.agencia}

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = await self.http.request(method, path, **kwargs)
        resp.raise_for_status()
        return resp.json()
