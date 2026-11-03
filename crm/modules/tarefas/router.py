from typing import Literal
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from crm.modules.tarefas.schemas import (
    Delegacao,
    MudancaDeStatus,
    NovaTarefa,
    TarefaOut,
)
from crm.modules.tarefas.service import TarefaService

router = APIRouter(prefix="/tarefas", tags=["tarefas"])


@router.post("", status_code=201)
@inject
async def criar(body: NovaTarefa, service: FromDishka[TarefaService]) -> TarefaOut:
    return await service.criar(
        body.titulo, body.cpf_cnpj, body.prazo, body.responsavel_ldap
    )


@router.get("")
@inject
async def listar(
    service: FromDishka[TarefaService],
    visao: Literal["minhas", "acompanhando"] = "minhas",
) -> list[TarefaOut]:
    return await service.listar(visao)


@router.post("/{tarefa_id}/delegar")
@inject
async def delegar(
    tarefa_id: UUID, body: Delegacao, service: FromDishka[TarefaService]
) -> TarefaOut:
    return await service.delegar(tarefa_id, body.responsavel_ldap)


@router.post("/{tarefa_id}/status")
@inject
async def mudar_status(
    tarefa_id: UUID, body: MudancaDeStatus, service: FromDishka[TarefaService]
) -> TarefaOut:
    return await service.mudar_status(tarefa_id, body.status)
