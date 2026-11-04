from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crm.modules.visitas.models import Visita


class VisitaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def adicionar(self, visita: Visita) -> None:
        self.session.add(visita)

    async def obter(self, visita_id: UUID) -> Visita | None:
        return await self.session.get(Visita, visita_id)

    async def listar_do_gerente(self, ldap: str) -> list[Visita]:
        consulta = select(Visita).where(Visita.gerente_ldap == ldap).order_by(Visita.data.desc())
        return list(await self.session.scalars(consulta))

    async def do_gerente_no_periodo(self, ldap: str, inicio: date, fim: date) -> list[Visita]:
        consulta = (
            select(Visita)
            .where(Visita.gerente_ldap == ldap, Visita.data.between(inicio, fim))
            .order_by(Visita.data)
        )
        return list(await self.session.scalars(consulta))

    async def commit(self) -> None:
        await self.session.commit()
