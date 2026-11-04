"""Percorre TODAS as rotas do OpenAPI sem login. Testa o comportamento (não a estrutura interna
do FastAPI): quem não responde 401 é rota aberta, e a lista de abertas tem de ser exatamente a
esperada. Rota pública nova exige mexer em PUBLICAS de propósito."""

import asyncio
import re
from uuid import uuid4

import httpx

from crm.main import app

PUBLICAS = {
    ("GET", "/health"),
    ("GET", "/auth/login"),
    ("GET", "/auth/callback"),
    ("POST", "/auth/logout"),
}
METODOS = {"get", "post", "put", "patch", "delete"}


def _rotas() -> list[tuple[str, str]]:
    return [
        (metodo.upper(), path)
        for path, ops in app.openapi()["paths"].items()
        for metodo in ops
        if metodo in METODOS
    ]


def _status_sem_login(cookies: dict | None = None) -> dict[tuple[str, str], int]:
    async def go() -> dict[tuple[str, str], int]:
        resultado = {}
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t", cookies=cookies
        ) as c:
            for metodo, path in _rotas():
                url = re.sub(r"\{[^}]+\}", str(uuid4()), path)
                # corpo vazio de propósito: o 401 tem de vir ANTES do 422 de validação
                r = await c.request(
                    metodo, url, headers={"X-Requested-With": "x"}, json={}, follow_redirects=False
                )
                resultado[(metodo, path)] = r.status_code
        return resultado

    return asyncio.run(go())


def test_o_teste_enxerga_as_rotas():
    assert len(_rotas()) > len(PUBLICAS)  # evita passar "no vazio"


def test_so_as_rotas_esperadas_ficam_abertas():
    abertas = {rota for rota, status in _status_sem_login().items() if status != 401}
    assert abertas == PUBLICAS


def test_cookie_invalido_nao_autentica():
    abertas = {
        rota for rota, status in _status_sem_login({"crm_session": "lixo"}).items() if status != 401
    }
    assert abertas == PUBLICAS
