from dishka import Provider, Scope, provide

from crm.modules.tarefas.repository import TarefaRepository
from crm.modules.tarefas.service import TarefaService


class TarefaProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(TarefaRepository)
    service = provide(TarefaService)
