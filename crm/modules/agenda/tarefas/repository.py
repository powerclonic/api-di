from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crm.modules.agenda.tarefas.models import Tarefa


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

    async def commit(self) -> None:
        await self.session.commit()
