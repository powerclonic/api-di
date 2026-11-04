from datetime import date
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crm.modules.tarefas.models import StatusTarefa, Tarefa


class TarefaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def adicionar(self, tarefa: Tarefa) -> None:
        self.session.add(tarefa)
        await self.session.flush()  # materializa o id antes de enviar ao Core

    async def obter(self, tarefa_id: UUID) -> Tarefa | None:
        return await self.session.get(Tarefa, tarefa_id)

    async def listar(self, ldap: str, visao: Literal["minhas", "acompanhando"]) -> list[Tarefa]:
        """minhas = eu executo; acompanhando = eu pedi e outra pessoa executa."""
        if visao == "minhas":
            filtro = Tarefa.responsavel_ldap == ldap
        else:
            filtro = (Tarefa.solicitante_ldap == ldap) & (Tarefa.responsavel_ldap != ldap)
        return list(await self.session.scalars(select(Tarefa).where(filtro)))

    async def pendentes_no_periodo(self, ldap: str, inicio: date, fim: date) -> list[Tarefa]:
        """Tarefas que eu executo, ainda não concluídas, com prazo dentro do período."""
        consulta = (
            select(Tarefa)
            .where(
                Tarefa.responsavel_ldap == ldap,
                Tarefa.status != StatusTarefa.CONCLUIDA,
                Tarefa.prazo.between(inicio, fim),
            )
            .order_by(Tarefa.prazo)
        )
        return list(await self.session.scalars(consulta))

    async def commit(self) -> None:
        await self.session.commit()
