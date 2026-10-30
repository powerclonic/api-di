from datetime import date
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crm.clients.core import CoreGateway
from crm.clients.datalake import DatalakeGateway
from crm.modules.tarefas.models import StatusTarefa, Tarefa
from crm.shared.auth import UsuarioAtual
from crm.shared.errors import AcessoNegado, NaoEncontrado, RegraDeNegocio


class TarefaService:
    def __init__(
        self,
        session: AsyncSession,
        core: CoreGateway,
        datalake: DatalakeGateway,
        usuario: UsuarioAtual,
    ):
        self.session = session
        self.core = core
        self.datalake = datalake
        self.usuario = usuario

    async def criar(
        self, titulo: str, prazo: date | None, responsavel_ldap: str | None
    ) -> Tarefa:
        responsavel = responsavel_ldap or self.usuario.ldap
        await self._validar_responsavel(responsavel)
        tarefa = Tarefa(
            titulo=titulo,
            prazo=prazo,
            solicitante_ldap=self.usuario.ldap,
            responsavel_ldap=responsavel,
        )
        self.session.add(tarefa)
        await self.session.flush()  # materializa o id antes de enviar ao Core
        await self.core.registrar_tarefa(tarefa)
        await self.session.commit()
        return tarefa

    async def listar(self, visao: Literal["minhas", "acompanhando"]) -> list[Tarefa]:
        """minhas = eu executo; acompanhando = eu pedi e outra pessoa executa."""
        ldap = self.usuario.ldap
        if visao == "minhas":
            filtro = Tarefa.responsavel_ldap == ldap
        else:
            filtro = (Tarefa.solicitante_ldap == ldap) & (Tarefa.responsavel_ldap != ldap)
        return list(await self.session.scalars(select(Tarefa).where(filtro)))

    async def delegar(self, tarefa_id: UUID, responsavel_ldap: str) -> Tarefa:
        tarefa = await self._obter(tarefa_id)
        if tarefa.solicitante_ldap != self.usuario.ldap:
            raise AcessoNegado("Só quem criou a tarefa pode delegá-la")
        await self._validar_responsavel(responsavel_ldap)
        tarefa.delegar(responsavel_ldap)
        await self.core.registrar_tarefa(tarefa)
        await self.session.commit()
        return tarefa

    async def mudar_status(self, tarefa_id: UUID, status: StatusTarefa) -> Tarefa:
        tarefa = await self._obter(tarefa_id)
        if tarefa.responsavel_ldap != self.usuario.ldap:
            raise AcessoNegado("Só o responsável atualiza o andamento")
        tarefa.status = status
        await self.core.registrar_tarefa(tarefa)
        await self.session.commit()
        return tarefa

    async def _obter(self, tarefa_id: UUID) -> Tarefa:
        tarefa = await self.session.get(Tarefa, tarefa_id)
        if tarefa is None:
            raise NaoEncontrado(f"Tarefa {tarefa_id} não encontrada")
        if self.usuario.ldap not in (tarefa.solicitante_ldap, tarefa.responsavel_ldap):
            raise AcessoNegado("Você não participa desta tarefa")
        return tarefa

    async def _validar_responsavel(self, ldap: str) -> None:
        if ldap == self.usuario.ldap:
            return
        if ldap not in await self.datalake.colaboradores_da_agencia():
            raise RegraDeNegocio(f"{ldap} não é da sua agência")
