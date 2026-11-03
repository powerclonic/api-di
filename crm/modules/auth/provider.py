from dishka import Provider, Scope, provide
from fastapi import HTTPException, Request

from crm.modules.auth.service import SessaoService
from crm.shared.auth import UsuarioAtual
from crm.shared.config import Settings


class AuthProvider(Provider):
    scope = Scope.REQUEST

    sessoes = provide(SessaoService)

    @provide
    async def usuario_atual(
        self, request: Request, sessoes: SessaoService, settings: Settings
    ) -> UsuarioAtual:
        cookie = request.cookies.get(settings.session_cookie_name)
        usuario = await sessoes.obter_usuario(cookie) if cookie else None
        if usuario is None:
            raise HTTPException(status_code=401, detail="Não autenticado")
        return usuario
