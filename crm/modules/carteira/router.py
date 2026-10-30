"""Carteira e aniversários. Sem regra de negócio: só repassa o que o datalake devolve,
por isso não tem service nem models."""

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query

from crm.clients.datalake import Associado, DatalakeGateway

router = APIRouter(prefix="/carteira", tags=["carteira"])


@router.get("")
@inject
async def carteira(datalake: FromDishka[DatalakeGateway]) -> list[Associado]:
    return await datalake.carteira()


@router.get("/aniversarios")
@inject
async def aniversarios(
    datalake: FromDishka[DatalakeGateway], mes: int = Query(ge=1, le=12)
) -> list[Associado]:
    return await datalake.aniversariantes(mes)
