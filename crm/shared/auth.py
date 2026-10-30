"""Quem está fazendo a requisição.

STUB de desenvolvimento: lê o LDAP do header X-Ldap.
O real: validar o JWT do Entra ID (assinatura via JWKS, iss, aud, exp, tid) e extrair o
LDAP do claim correto. O resto do app só enxerga UsuarioAtual, então nada mais muda.

O LDAP vem SEMPRE do token, nunca de parâmetro da requisição: o Core confia em qualquer
LDAP que a gente enviar, então este é o único ponto de controle."""

from dataclasses import dataclass

from dishka import Provider, Scope, provide
from fastapi import HTTPException, Request


@dataclass(frozen=True)
class UsuarioAtual:
    ldap: str
    nome: str


class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def usuario_atual(self, request: Request) -> UsuarioAtual:
        ldap = request.headers.get("x-ldap")
        if not ldap:
            raise HTTPException(status_code=401, detail="Header X-Ldap ausente (modo dev)")
        return UsuarioAtual(ldap=ldap, nome=ldap.title())
