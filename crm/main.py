"""Rodar:  docker compose up -d && uv run alembic upgrade heads && uv run uvicorn crm.main:app --reload

Front: http://localhost:8000/ (login via Entra mock em :8001; ou /auth/login) (Entra mock em :8001). Requisições que alteram estado
precisam do header X-Requested-With."""

from pathlib import Path

from dishka import Provider
from dishka.integrations.fastapi import setup_dishka
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from crm.container import create_container
from crm.shared.auth import protecao_csrf
from crm.shared.discovery import discover_routers
from crm.shared.errors import AcessoNegado, NaoEncontrado, RegraDeNegocio

STATUS_POR_ERRO = {NaoEncontrado: 404, AcessoNegado: 403, RegraDeNegocio: 422}


async def erro_de_negocio(_: Request, exc: Exception) -> JSONResponse:
    status = next(s for tipo, s in STATUS_POR_ERRO.items() if isinstance(exc, tipo))
    return JSONResponse({"detail": str(exc)}, status_code=status)


def create_app(*extra_providers: Provider) -> FastAPI:
    app = FastAPI(title="CRM - MVP", dependencies=[Depends(protecao_csrf)])
    for router in discover_routers():
        app.include_router(router)
    for erro in STATUS_POR_ERRO:
        app.add_exception_handler(erro, erro_de_negocio)

    @app.get("/health", tags=["infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Front estático na mesma origem do BFF: cookie de sessão sem CORS. Precisa ser o último mount.
    app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True))

    setup_dishka(create_container(*extra_providers), app)
    return app


app = create_app()
