"""Quem está fazendo a requisição.

O resto do app só enxerga UsuarioAtual. Quem o monta é o AuthProvider (modules/auth/provider.py),
a partir do cookie de sessão do BFF. O LDAP vem SEMPRE da sessão (que veio do id_token validado),
nunca de parâmetro da requisição: o Core confia em qualquer LDAP que a gente enviar, então este
é o único ponto de controle."""

from dataclasses import dataclass

from fastapi import HTTPException, Request

from crm.shared.errors import AcessoNegado


@dataclass(frozen=True)
class UsuarioAtual:
    ldap: str
    nome: str
    agencia: str | None = None
    roles: tuple[str, ...] = ()

    def exigir_role(self, *roles: str) -> None:
        """Dentro dos services: AcessoNegado vira 403."""
        if not set(roles) & set(self.roles):
            raise AcessoNegado(f"Requer um dos perfis: {', '.join(roles)}")


async def protecao_csrf(request: Request) -> None:
    """O cookie é SameSite=Lax; isto fecha o resto. Um formulário de outro site não consegue
    mandar header customizado, e um fetch cross-origin com ele cai no preflight do CORS."""
    if request.method not in {"GET", "HEAD", "OPTIONS"} and not request.headers.get("x-requested-with"):
        raise HTTPException(403, "Header X-Requested-With obrigatório em requisições que alteram estado")


async def rota_publica() -> None:
    """Marcador: `dependencies=[Depends(rota_publica)]` na rota a isenta do login obrigatório."""


async def exigir_login(request: Request) -> None:
    """Dependência GLOBAL do app: toda rota exige sessão, exceto as marcadas com `rota_publica`.
    Rota nova nasce protegida; esquecer de proteger deixa de ser possível. Roda antes da validação
    do corpo, então quem não está logado recebe 401 e não 422."""
    route = request.scope.get("route")
    if route is not None and any(d.call is rota_publica for d in route.dependant.dependencies):
        return
    await request.state.dishka_container.get(UsuarioAtual)  # 401 se não houver sessão válida
