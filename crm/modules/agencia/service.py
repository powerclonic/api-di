from crm.clients.core.tarefas import Tarefa, TarefasGateway


class AgenciaService:
    def __init__(self, core: TarefasGateway):
        self.core = core

    async def tarefas_da_agencia(self) -> list[Tarefa]:
        """Todas as tarefas da agência do usuário (visitas incluídas: no Core é a mesma coisa).
        O acesso (só administrador) é exigido no router. A agência vem da sessão, via
        TarefasGateway: nunca de parâmetro."""
        return await self.core.buscar()
