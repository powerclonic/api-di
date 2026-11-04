from dishka import Provider, Scope, provide

from crm.clients.core.associados import AssociadosGateway, AssociadosHttpx
from crm.clients.core.colaboradores import ColaboradoresGateway, ColaboradoresHttpx
from crm.clients.core.tarefas import TarefasGateway, TarefasHttpx
from crm.clients.entra import EntraGateway, EntraHttpx


class ClientsProvider(Provider):
    """Trocar um sistema externo = trocar UMA linha aqui."""

    core_tarefas = provide(TarefasHttpx, provides=TarefasGateway, scope=Scope.REQUEST)
    core_colaboradores = provide(
        ColaboradoresHttpx, provides=ColaboradoresGateway, scope=Scope.REQUEST
    )
    core_associados = provide(AssociadosHttpx, provides=AssociadosGateway, scope=Scope.REQUEST)
    entra = provide(EntraHttpx, provides=EntraGateway, scope=Scope.APP)
