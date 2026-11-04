from datetime import date

from crm.modules.agenda.contracts import ItemDeAgenda
from crm.modules.tarefas.repository import TarefaRepository


class FonteTarefas:
    """Implementa `FonteDeAgenda`: tarefas pendentes do gerente, pelo prazo."""

    def __init__(self, repository: TarefaRepository):
        self.repository = repository

    async def itens(self, ldap: str, inicio: date, fim: date) -> list[ItemDeAgenda]:
        tarefas = await self.repository.pendentes_no_periodo(ldap, inicio, fim)
        return [
            ItemDeAgenda(
                origem="tarefa",
                id=str(t.id),
                titulo=t.titulo,
                data=t.prazo,  # type: ignore[arg-type]  # a consulta só traz quem tem prazo
                cpf_cnpj=t.cpf_cnpj,
            )
            for t in tarefas
        ]
