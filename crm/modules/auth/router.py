import secrets
import time

import jwt
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from crm.clients.entra import EntraGateway, FalhaDeAutenticacao
from crm.modules.auth.service import SessaoService
from crm.shared.auth import UsuarioAtual, rota_publica
from crm.shared.config import Settings

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_LOGIN = "crm_oauth"  # state + nonce + PKCE entre /login e /callback
LOGIN_TTL = 600


class UsuarioOut(BaseModel):
    ldap: str
    nome: str
    agencia: str | None
    roles: list[str]


class LogoutOut(BaseModel):
    logout_url: str  # o front navega para cá para encerrar também a sessão no Entra


def _cookie(settings: Settings) -> dict:
    return {"httponly": True, "samesite": "lax", "secure": settings.session_cookie_secure}


@router.get("/login", dependencies=[Depends(rota_publica)])
@inject
async def login(entra: FromDishka[EntraGateway], settings: FromDishka[Settings]) -> RedirectResponse:
    state, nonce, verifier = (secrets.token_urlsafe(n) for n in (32, 32, 48))
    pendente = jwt.encode(
        {"state": state, "nonce": nonce, "verifier": verifier, "exp": int(time.time()) + LOGIN_TTL},
        settings.session_secret,
        algorithm="HS256",
    )
    resp = RedirectResponse(entra.url_login(state, nonce, verifier), status_code=302)
    resp.set_cookie(COOKIE_LOGIN, pendente, max_age=LOGIN_TTL, path="/auth", **_cookie(settings))
    return resp


@router.get("/callback", dependencies=[Depends(rota_publica)])
@inject
async def callback(
    request: Request,
    entra: FromDishka[EntraGateway],
    sessoes: FromDishka[SessaoService],
    settings: FromDishka[Settings],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    if error:
        raise HTTPException(401, f"{error}: {error_description or ''}")
    try:
        pendente = jwt.decode(
            request.cookies.get(COOKIE_LOGIN, ""), settings.session_secret, algorithms=["HS256"]
        )
    except jwt.PyJWTError:
        raise HTTPException(400, "Login expirado ou inexistente; comece por /auth/login") from None
    if not code or not state or not secrets.compare_digest(state, pendente["state"]):
        raise HTTPException(400, "state inválido")

    try:
        tokens = await entra.trocar_code(code, pendente["verifier"])
        claims = await entra.validar_id_token(tokens.id_token, nonce=pendente["nonce"])
        valor = await sessoes.criar(claims, tokens)
    except FalhaDeAutenticacao as exc:
        raise HTTPException(401, str(exc)) from exc

    resp = RedirectResponse(settings.frontend_url, status_code=302)
    resp.delete_cookie(COOKIE_LOGIN, path="/auth")
    resp.set_cookie(
        settings.session_cookie_name, valor, max_age=settings.session_ttl_segundos, path="/", **_cookie(settings)
    )
    return resp


@router.get("/me")
@inject
async def me(usuario: FromDishka[UsuarioAtual]) -> UsuarioOut:
    return UsuarioOut(
        ldap=usuario.ldap, nome=usuario.nome, agencia=usuario.agencia, roles=list(usuario.roles)
    )


@router.post("/logout", dependencies=[Depends(rota_publica)])
@inject
async def logout(
    request: Request,
    response: Response,
    entra: FromDishka[EntraGateway],
    sessoes: FromDishka[SessaoService],
    settings: FromDishka[Settings],
) -> LogoutOut:
    if cookie := request.cookies.get(settings.session_cookie_name):
        await sessoes.encerrar(cookie)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return LogoutOut(logout_url=entra.url_logout(settings.frontend_url))
