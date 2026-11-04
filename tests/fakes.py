"""Fakes em memória das fronteiras do app (banco e Core). Sem I/O, para testes de service."""

from datetime import date
from uuid import UUID, uuid4

from crm.clients.core import StatusCore
from crm.clients.core import Tarefa as TarefaCore
from crm.modules.tarefas.models import StatusTarefa, Tarefa


class FakeTarefaRepository:
    def __init__(self, *tarefas: Tarefa):
        self.tarefas: dict[UUID, Tarefa] = {}
        for t in tarefas:
            self._flush(t)
        self.commits = 0

    def _flush(self, tarefa: Tarefa) -> None:
        """Os defaults de coluna (id, status) do SQLAlchemy só rodam no flush; o fake imita isso."""
        tarefa.id = tarefa.id or uuid4()
        tarefa.status = tarefa.status or StatusTarefa.ABERTA
        self.tarefas[tarefa.id] = tarefa

    async def adicionar(self, tarefa: Tarefa) -> None:
        self._flush(tarefa)

    async def obter(self, tarefa_id: UUID) -> Tarefa | None:
        return self.tarefas.get(tarefa_id)

    async def listar(self, ldap, visao):
        if visao == "minhas":
            return [t for t in self.tarefas.values() if t.responsavel_ldap == ldap]
        return [
            t
            for t in self.tarefas.values()
            if t.solicitante_ldap == ldap and t.responsavel_ldap != ldap
        ]

    async def commit(self) -> None:
        self.commits += 1


class FakeCore:
    """Implementa CoreGateway e registra as chamadas para os testes inspecionarem."""

    def __init__(self):
        self.registradas: list[TarefaCore] = []
        self.edicoes: list[tuple[str, str, StatusCore | None, date | None]] = []

    async def registrar(self, tarefa: TarefaCore) -> TarefaCore:
        self.registradas.append(tarefa)
        return tarefa

    async def buscar(self, **_):
        return []

    async def editar(self, source_external_id, suid, *, status=None, plan_end=None, description=None):
        self.edicoes.append((source_external_id, suid, status, plan_end))
