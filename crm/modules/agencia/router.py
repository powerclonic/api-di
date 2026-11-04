from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from crm.modules.agencia.permissoes import ADMINISTRADOR
from crm.modules.agencia.schemas import TarefaAgenciaOut
from crm.modules.agencia.service import AgenciaService
from crm.shared.auth import requer_role

router = APIRouter(
    prefix="/agencia", tags=["agencia"], dependencies=[requer_role(ADMINISTRADOR)]
)


@router.get("/tarefas")
@inject
async def tarefas(service: FromDishka[AgenciaService]) -> list[TarefaAgenciaOut]:
    return await service.tarefas_da_agencia()
