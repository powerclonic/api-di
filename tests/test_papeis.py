"""Perfis. Não há piso global (cada domínio tem os seus roles), então são dois testes:
1) estrutural: toda rota protegida declara `requer_role` ou `rota_sem_papel`; esquecer = falha;
2) comportamento, pelas rotas de verdade, logado e sem tocar em banco nem Core."""

import asyncio
import re
from uuid import uuid4

import httpx
from dishka import Provider, Scope, provide
from fastapi.routing import APIRoute

from crm.main import create_app
from crm.modules.agencia.permissoes import ADMINISTRADOR, OPERADOR
from crm.shared.auth import UsuarioAtual, requer_role, rota_publica, rota_sem_papel
from tests.test_rotas_protegidas import METODOS, PUBLICAS

SO_LOGIN = {("GET", "/auth/me")}  # rota_sem_papel


def _declaracoes(route: APIRoute) -> tuple[bool, bool, bool]:
    calls = [d.call for d in route.dependant.dependencies]
    return (
        rota_publica in calls,
        rota_sem_papel in calls,
        any(hasattr(c, "roles") for c in calls),
    )


def test_toda_rota_protegida_declara_seus_roles():
    sem_declaracao = []
    for route in create_app().routes:
        if not isinstance(route, APIRoute):
            continue
        publica, so_login, com_role = _declaracoes(route)
        if not (publica or so_login or com_role):
            sem_declaracao.append(route.path)
    assert not sem_declaracao, f"rotas sem requer_role/rota_sem_papel: {sem_declaracao}"


def test_requer_role_e_o_marcador_que_o_teste_procura():
    assert hasattr(requer_role("x").dependency, "roles")


def _status(*roles: str, so_prefixo: str = "") -> dict[tuple[str, str], int]:
    class Logado(Provider):
        @provide(scope=Scope.REQUEST)
        def usuario(self) -> UsuarioAtual:
            return UsuarioAtual(ldap="ana", nome="Ana", agencia="0001", roles=roles)

    app = create_app(Logado())
    rotas = [
        (m.upper(), p)
        for p, ops in app.openapi()["paths"].items()
        for m in ops
        if m in METODOS and (m.upper(), p) not in PUBLICAS and p.startswith(so_prefixo)
    ]

    async def go() -> dict[tuple[str, str], int]:
        resultado = {}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            for metodo, path in rotas:
                url = re.sub(r"\{[^}]+\}", str(uuid4()), path)
                try:
                    r = await c.request(metodo, url, headers={"X-Requested-With": "x"}, json={})
                    resultado[(metodo, path)] = r.status_code
                except Exception:  # passou pelos perfis e quebrou adiante (banco/Core inexistentes)
                    resultado[(metodo, path)] = 500
        return resultado

    return asyncio.run(go())


def test_sem_perfil_ou_com_perfil_de_outro_dominio_so_passa_o_so_login():
    for roles in [(), ("sede_credito_administrador",)]:
        liberadas = {rota for rota, s in _status(*roles).items() if s != 403}
        assert liberadas == SO_LOGIN


def test_operador_nao_entra_na_agencia_mas_entra_no_resto():
    status = _status(OPERADOR)
    barradas = {rota for rota, s in status.items() if s == 403}
    assert barradas == {rota for rota in status if rota[1].startswith("/agencia")}


def test_administrador_sozinho_nao_e_barrado_por_perfil():
    assert not {r for r, s in _status(ADMINISTRADOR).items() if s == 403}
