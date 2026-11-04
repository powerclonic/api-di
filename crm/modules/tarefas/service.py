from datetime import date
from typing import Literal
from uuid import UUID

from crm.clients.core.tarefas import TarefasGateway
from crm.modules.tarefas.mappers import para_api, status_para_api
from crm.modules.tarefas.models import StatusTarefa, Tarefa
from crm.modules.tarefas.repository import TarefaRepository
from crm.shared.auth import UsuarioAtual
from crm.shared.errors import AcessoNegado, NaoEncontrado


class TarefaService:
    def __init__(
        self,
        repository: TarefaRepository,
        core: TarefasGateway,
        usuario: UsuarioAtual,
    ):
        self.repository = repository
        self.core = core
        self.usuario = usuario

    async def criar(
        self,
        titulo: str,
        cpf_cnpj: str,
        prazo: date | None,
        responsavel_ldap: str | None,
    ) -> Tarefa:
        responsavel = responsavel_ldap or self.usuario.ldap
        tarefa = Tarefa(
            titulo=titulo,
            cpf_cnpj=cpf_cnpj,
            prazo=prazo,
            solicitante_ldap=self.usuario.ldap,
            responsavel_ldap=responsavel,
        )
        await self.repository.adicionar(tarefa)
        await self.core.registrar(para_api(tarefa))
        await self.repository.commit()
        return tarefa

    async def listar(self, visao: Literal["minhas", "acompanhando"]) -> list[Tarefa]:
        return await self.repository.listar(self.usuario.ldap, visao)

    async def delegar(self, tarefa_id: UUID, responsavel_ldap: str) -> Tarefa:
        tarefa = await self._obter(tarefa_id)
        if tarefa.solicitante_ldap != self.usuario.ldap:
            raise AcessoNegado("Só quem criou a tarefa pode delegá-la")
        tarefa.delegar(responsavel_ldap)
        # PATCH do Core não aceita `owner`: a delegação, por ora, só existe aqui.
        await self.repository.commit()
        return tarefa

    async def mudar_status(self, tarefa_id: UUID, status: StatusTarefa) -> Tarefa:
        tarefa = await self._obter(tarefa_id)
        if tarefa.responsavel_ldap != self.usuario.ldap:
            raise AcessoNegado("Só o responsável atualiza o andamento")
        tarefa.status = status
        if status != StatusTarefa.ABERTA:  # o PATCH do Core não aceita voltar para OPEN
            await self.core.editar(
                str(tarefa.id), tarefa.cpf_cnpj, status=status_para_api(status)
            )
        await self.repository.commit()
        return tarefa

    async def _obter(self, tarefa_id: UUID) -> Tarefa:
        tarefa = await self.repository.obter(tarefa_id)
        if tarefa is None:
            raise NaoEncontrado(f"Tarefa {tarefa_id} não encontrada")
        if self.usuario.ldap not in (tarefa.solicitante_ldap, tarefa.responsavel_ldap):
            raise AcessoNegado("Você não participa desta tarefa")
        return tarefa
