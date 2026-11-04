"""Core (CRM sistêmico): API de tarefas. Visita e tarefa são a MESMA entidade lá; o que as
diferencia é o campo `type`.

Client comum: não conhece nenhum módulo do app. Fala em termos do DTO `Tarefa` (espelho do que
a API entende) e expõe registrar / buscar / editar. Quem traduz Visita ou Tarefa do nosso domínio
para este DTO são os mappers de cada módulo (`para_api`).

`organization` e `branch` (contexto da chamada) vêm de http.py; `suid` (CPF/CNPJ do associado)
faz parte do DTO. O id do nosso lado vai como `sourceExternalId`, então o Core reconhece o mesmo
registro entre tentativas."""

from datetime import date
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from crm.clients.core.http import CoreHttpxBase

RECURSO = "/tarefas/v1"


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


class TarefasGateway(Protocol):
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


class TarefasHttpx(CoreHttpxBase, TarefasGateway):
    async def registrar(self, tarefa: Tarefa) -> Tarefa:
        body = {
            **tarefa.model_dump(by_alias=True, mode="json", exclude_none=True),
            **self._filtro(),
        }
        return self._tarefa(await self._request("POST", RECURSO, json=body))

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
            "GET", RECURSO, params={k: v for k, v in params.items() if v is not None}
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
        await self._request("PATCH", RECURSO, json=body)

    @staticmethod
    def _tarefa(dados: dict[str, Any]) -> Tarefa:
        return Tarefa.model_validate({k: v for k, v in dados.items() if v is not None})
