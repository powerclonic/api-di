"""Rodar:  uv run uvicorn crm.main:app --reload

Em dev, mande o header  X-Ldap: gerente1   (usuários do stub: gerente1, assistente1, assistente2)"""

from dishka import Provider
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from crm.container import create_container
from crm.modules.carteira.router import router as carteira
from crm.modules.tarefas.router import router as tarefas
from crm.modules.visitas.router import router as visitas
from crm.shared.errors import AcessoNegado, NaoEncontrado, RegraDeNegocio

STATUS_POR_ERRO = {NaoEncontrado: 404, AcessoNegado: 403, RegraDeNegocio: 422}


async def erro_de_negocio(_: Request, exc: Exception) -> JSONResponse:
    status = next(s for tipo, s in STATUS_POR_ERRO.items() if isinstance(exc, tipo))
    return JSONResponse({"detail": str(exc)}, status_code=status)


def create_app(*extra_providers: Provider) -> FastAPI:
    app = FastAPI(title="CRM - MVP")
    for router in (visitas, tarefas, carteira):
        app.include_router(router)
    for erro in STATUS_POR_ERRO:
        app.add_exception_handler(erro, erro_de_negocio)

    @app.get("/health", tags=["infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    setup_dishka(create_container(*extra_providers), app)
    return app


app = create_app()
