"""Core (CRM sistêmico): API de tarefas. Visita e tarefa são a MESMA entidade lá; o que as
diferencia é o campo `type`.

Client comum: não conhece nenhum módulo do app. Fala em termos do DTO `Tarefa` (espelho do que
a API entende) e expõe registrar / buscar / editar. Quem traduz Visita ou Tarefa do nosso domínio
para este DTO são os mappers de cada módulo (`para_api`).

`organization` (Settings) e `branch` (agência do usuário) são contexto da chamada e
preenchidos aqui; `suid` (CPF/CNPJ do associado) faz parte do DTO. O id do nosso lado vai como `sourceExternalId`, então o Core reconhece o mesmo
registro entre tentativas."""

import time
from collections.abc import AsyncGenerator
from datetime import date
from enum import StrEnum
from typing import Any, NewType, Protocol

import httpx
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from crm.shared.auth import UsuarioAtual
from crm.shared.config import Settings
from crm.shared.errors import RegraDeNegocio


class StatusCore(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"  # a API só aceita na edição


class Tarefa(BaseModel):
    """DTO da API do Core (snake_case aqui, camelCase no fio)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source_external_id: str
    suid: str  # CPF/CNPJ do associado a que a tarefa se refere
    title: str
    type: str | None = None  # "visita" | "tarefa"
    description: str | None = None
    owner: str | None = None  # LDAP
    plan_end: date | None = None
    status: StatusCore = StatusCore.OPEN


class CoreGateway(Protocol):
    async def registrar(self, tarefa: Tarefa) -> Tarefa: ...

    async def buscar(
        self,
        *,
        source_external_id: str | None = None,
        tipo: list[str] | None = None,
        owner: str | None = None,
    ) -> list[Tarefa]: ...

    async def editar(
        self,
        source_external_id: str,
        suid: str,
        *,
        status: StatusCore | None = None,
        plan_end: date | None = None,
        description: str | None = None,
    ) -> None: ...


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


class CoreHttpx(CoreGateway):
    """Um por requisição: carrega o usuário (agência = `branch`). O client HTTP (base_url e
    autenticação) vem pronto do container."""

    def __init__(self, http: CoreHttp, settings: Settings, usuario: UsuarioAtual):
        self.http = http
        self.s = settings
        self.usuario = usuario

    async def registrar(self, tarefa: Tarefa) -> Tarefa:
        body = {
            **tarefa.model_dump(by_alias=True, mode="json", exclude_none=True),
            **self._filtro(),
        }
        return self._tarefa(await self._request("POST", json=body))

    async def buscar(
        self,
        *,
        source_external_id: str | None = None,
        tipo: list[str] | None = None,
        owner: str | None = None,
    ) -> list[Tarefa]:
        params = {
            **self._filtro(),
            "sourceExternalId": source_external_id,
            "type": tipo,
            "owner": owner,
        }
        dados = await self._request(
            "GET", params={k: v for k, v in params.items() if v is not None}
        )
        return [self._tarefa(item) for item in dados]

    async def editar(
        self,
        source_external_id: str,
        suid: str,
        *,
        status: StatusCore | None = None,
        plan_end: date | None = None,
        description: str | None = None,
    ) -> None:
        campos = {"status": status, "planEnd": plan_end, "description": description}
        body = {
            **self._filtro(),
            "suid": suid,
            "sourceExternalId": source_external_id,
            **{k: v for k, v in campos.items() if v is not None},
        }
        await self._request("PATCH", json=body)

    # --- HTTP ---------------------------------------------------------------
    def _filtro(self) -> dict[str, str]:
        if not self.usuario.agencia:
            raise RegraDeNegocio("Usuário sem agência: não dá para chamar o Core")
        return {"organization": self.s.api_organization, "branch": self.usuario.agencia}

    @staticmethod
    def _tarefa(dados: dict[str, Any]) -> Tarefa:
        return Tarefa.model_validate({k: v for k, v in dados.items() if v is not None})

    async def _request(self, method: str, **kwargs: Any) -> Any:
        resp = await self.http.request(method, "/tarefas/v1", **kwargs)
        print(resp.json())
        resp.raise_for_status()
        return resp.json()
