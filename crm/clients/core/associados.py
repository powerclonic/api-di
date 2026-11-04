"""Core: API de associados (somente leitura). Não filtra por organization/branch: os filtros
são os próprios query params (`agencia`, `carteira`, `nome`)."""

from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from crm.clients.core.http import CoreHttpxBase

RECURSO = "/associados/v1"


class Associado(BaseModel):
    """DTO da API do Core (snake_case aqui, camelCase no fio)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cpf_cnpj: str
    nome: str
    agencia: str
    aniversario: str
    organization: str
    carteira: str | None = None
    tipo_pessoa: str | None = None


class AssociadosGateway(Protocol):
    async def listar(
        self,
        *,
        agencia: str | None = None,
        carteira: str | None = None,
        nome: str | None = None,
    ) -> list[Associado]: ...

    async def obter(self, cpf_cnpj: str) -> Associado | None: ...


class AssociadosHttpx(CoreHttpxBase, AssociadosGateway):
    async def listar(
        self,
        *,
        agencia: str | None = None,
        carteira: str | None = None,
        nome: str | None = None,
    ) -> list[Associado]:
        params = {"agencia": agencia, "carteira": carteira, "nome": nome}
        dados = await self._request(
            "GET", RECURSO, params={k: v for k, v in params.items() if v is not None}
        )
        return [self._associado(item) for item in dados]

    async def obter(self, cpf_cnpj: str) -> Associado | None:
        try:
            return self._associado(await self._request("GET", f"{RECURSO}/{cpf_cnpj}"))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    @staticmethod
    def _associado(dados: dict[str, Any]) -> Associado:
        return Associado.model_validate({k: v for k, v in dados.items() if v is not None})
