from datetime import date

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from crm.modules.agenda.schemas import ItemDeAgendaOut
from crm.modules.agenda.service import AgendaService

router = APIRouter(prefix="/agenda", tags=["agenda"])


@router.get("")
@inject
async def do_periodo(
    inicio: date, fim: date, service: FromDishka[AgendaService]
) -> list[ItemDeAgendaOut]:
    return await service.do_periodo(inicio, fim)
