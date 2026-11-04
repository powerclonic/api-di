from dishka import Provider, Scope, provide

from crm.modules.agenda.tarefas.repository import TarefaRepository
from crm.modules.agenda.tarefas.service import TarefaService


class TarefaProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(TarefaRepository)
    service = provide(TarefaService)
