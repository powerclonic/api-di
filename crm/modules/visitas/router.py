from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from crm.modules.visitas.relato import RelatoEstruturado
from crm.modules.visitas.schemas import NovaVisita, VisitaOut
from crm.modules.visitas.service import VisitaService

router = APIRouter(prefix="/visitas", tags=["visitas"])


@router.post("", status_code=201)
@inject
async def registrar(body: NovaVisita, service: FromDishka[VisitaService]) -> VisitaOut:
    return await service.registrar(body.cpf_cnpj, body.data, body.relato)


@router.get("")
@inject
async def listar(service: FromDishka[VisitaService]) -> list[VisitaOut]:
    return await service.listar()


@router.get("/{visita_id}")
@inject
async def obter(visita_id: UUID, service: FromDishka[VisitaService]) -> VisitaOut:
    return await service.obter(visita_id)


@router.put("/{visita_id}/relato")
@inject
async def editar_relato(
    visita_id: UUID, relato: RelatoEstruturado, service: FromDishka[VisitaService]
) -> VisitaOut:
    return await service.editar_relato(visita_id, relato)


@router.post("/{visita_id}/confirmar")
@inject
async def confirmar(visita_id: UUID, service: FromDishka[VisitaService]) -> VisitaOut:
    return await service.confirmar(visita_id)
