from dishka import Provider, Scope, provide

from crm.modules.visitas.repository import VisitaRepository
from crm.modules.visitas.service import VisitaService


class VisitaProvider(Provider):
    scope = Scope.REQUEST  # dependem do usuário atual e da sessão

    repository = provide(VisitaRepository)
    service = provide(VisitaService)
