"""Container de injeção de dependência (o "Service Provider" do app).

É o único lugar que decide qual implementação atende cada interface de clients/."""

from collections.abc import AsyncIterator

import httpx
from dishka import Provider, Scope, make_async_container, provide
from dishka.async_container import AsyncContainer
from dishka.integrations.fastapi import FastapiProvider
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from crm.clients.core.http import CoreAuth, CoreHttp
from crm.clients.provider import ClientsProvider
from crm.shared.config import Settings
from crm.shared.discovery import discover_providers


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
    async def core_http(self, settings: Settings) -> AsyncIterator[CoreHttp]:
        auth = CoreAuth(settings.api_url, settings.api_key, settings.api_secret)
        async with httpx.AsyncClient(base_url=settings.api_url, auth=auth, timeout=10) as http:
            yield CoreHttp(http)

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session


def create_container(*extra_providers: Provider) -> AsyncContainer:
    """`extra_providers` sobrescreve bindings (ex.: um TarefasGateway falho em testes)."""
    return make_async_container(
        FastapiProvider(),
        InfraProvider(),
        ClientsProvider(),
        *discover_providers(),  # crm/modules/**/provider.py
        *extra_providers,
    )
