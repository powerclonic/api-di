"""Container de injeção de dependência (o "Service Provider" do app).

É o único lugar que decide qual implementação atende cada interface de clients/."""

from collections.abc import AsyncIterator

from dishka import Provider, Scope, make_async_container, provide
from dishka.async_container import AsyncContainer
from dishka.integrations.fastapi import FastapiProvider
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from crm.clients.core import CoreFake, CoreGateway
from crm.clients.datalake import DatalakeFake, DatalakeGateway
from crm.clients.ia import IaFake, IaGateway
from crm.modules.tarefas.service import TarefaService
from crm.modules.visitas.service import VisitaService
from crm.shared.auth import AuthProvider
from crm.shared.config import Settings


class InfraProvider(Provider):
    """APP = um por processo. REQUEST = um por requisição."""

    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return Settings()

    @provide(scope=Scope.APP)
    async def engine(self, settings: Settings) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(settings.database_url)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session


class ClientsProvider(Provider):
    """Trocar um sistema externo = trocar UMA linha aqui.
    Ex.: CoreFake -> CoreApi (ou CoreRpa), IaFake -> IaLangChain."""

    core = provide(CoreFake, provides=CoreGateway, scope=Scope.REQUEST)
    datalake = provide(DatalakeFake, provides=DatalakeGateway, scope=Scope.REQUEST)
    ia = provide(IaFake, provides=IaGateway, scope=Scope.APP)


class ServicesProvider(Provider):
    scope = Scope.REQUEST  # dependem do usuário atual e da sessão

    visitas = provide(VisitaService)
    tarefas = provide(TarefaService)


def create_container(*extra_providers: Provider) -> AsyncContainer:
    """`extra_providers` sobrescreve bindings (ex.: um CoreGateway falho em testes)."""
    return make_async_container(
        FastapiProvider(),
        AuthProvider(),
        InfraProvider(),
        ClientsProvider(),
        ServicesProvider(),
        *extra_providers,
    )
