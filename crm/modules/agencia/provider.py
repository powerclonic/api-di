from dishka import Provider, Scope, provide

from crm.modules.agencia.service import AgenciaService


class AgenciaProvider(Provider):
    scope = Scope.REQUEST

    service = provide(AgenciaService)
