from dishka import Provider, Scope, provide

from crm.modules.agenda.contracts import FonteDeAgenda
from crm.modules.tarefas.fonte import FonteTarefas
from crm.modules.tarefas.repository import TarefaRepository
from crm.modules.tarefas.service import TarefaService


class TarefaProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(TarefaRepository)
    service = provide(TarefaService)
    fonte = provide(FonteTarefas, provides=FonteDeAgenda)  # alimenta a agenda
