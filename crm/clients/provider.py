from dishka import Provider, Scope, provide

from crm.clients.core import CoreGateway, CoreHttpx
from crm.clients.entra import EntraGateway, EntraHttpx


class ClientsProvider(Provider):
    """Trocar um sistema externo = trocar UMA linha aqui."""

    core = provide(CoreHttpx, provides=CoreGateway, scope=Scope.REQUEST)
    entra = provide(EntraHttpx, provides=EntraGateway, scope=Scope.APP)
