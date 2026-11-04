from dishka import Provider, Scope, collect, provide

from crm.modules.agenda.contracts import FonteDeAgenda
from crm.modules.agenda.service import AgendaService


class AgendaProvider(Provider):
    scope = Scope.REQUEST

    fontes = collect(FonteDeAgenda)  # list[FonteDeAgenda]: todas as fontes de todos os módulos
    service = provide(AgendaService)
