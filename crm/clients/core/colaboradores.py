"""Core: API de colaboradores (somente leitura). Filtros são query params (`agencia`, `cargo`,
`carteira`); o identificador é o LDAP."""

from enum import StrEnum
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from crm.clients.core.http import CoreHttpxBase

RECURSO = "/colaboradores/v1"


class Cargo(StrEnum):
    GERENTE_NEGOCIOS = "GERENTE_NEGOCIOS"
    GERENTE_AGENCIA = "GERENTE_AGENCIA"


class Colaborador(BaseModel):
    """DTO da API do Core (snake_case aqui, camelCase no fio)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    ldap: str
    nome: str
    agencia: str
    cargo: Cargo
    organization: str
    carteira: str | None = None


class ColaboradoresGateway(Protocol):
    async def listar(
        self,
        *,
        agencia: str | None = None,
        cargo: Cargo | None = None,
        carteira: str | None = None,
    ) -> list[Colaborador]: ...

    async def obter(self, ldap: str) -> Colaborador | None: ...


class ColaboradoresHttpx(CoreHttpxBase, ColaboradoresGateway):
    async def listar(
        self,
        *,
        agencia: str | None = None,
        cargo: Cargo | None = None,
        carteira: str | None = None,
    ) -> list[Colaborador]:
        params = {"agencia": agencia, "cargo": cargo, "carteira": carteira}
        dados = await self._request(
            "GET", RECURSO, params={k: v for k, v in params.items() if v is not None}
        )
        return [self._colaborador(item) for item in dados]

    async def obter(self, ldap: str) -> Colaborador | None:
        try:
            return self._colaborador(await self._request("GET", f"{RECURSO}/{ldap}"))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    @staticmethod
    def _colaborador(dados: dict[str, Any]) -> Colaborador:
        return Colaborador.model_validate({k: v for k, v in dados.items() if v is not None})
