import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from crm.clients.entra import EntraGateway, FalhaDeAutenticacao, Tokens
from crm.modules.auth.models import Sessao, Usuario, agora
from crm.shared.auth import UsuarioAtual
from crm.shared.config import Settings


def _hash(valor_do_cookie: str) -> str:
    return hashlib.sha256(valor_do_cookie.encode()).hexdigest()


def _de_epoch(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, UTC)


class SessaoService:
    def __init__(self, session: AsyncSession, entra: EntraGateway, settings: Settings):
        self.session = session
        self.entra = entra
        self.settings = settings

    async def criar(self, claims: dict[str, Any], tokens: Tokens) -> str:
        """Devolve o valor para o cookie (o banco só guarda o hash)."""
        agora_ = agora()
        await self.session.execute(delete(Sessao).where(Sessao.expira_em < agora_))  # limpeza barata

        campos = self._campos(claims)
        await self._upsert_usuario(campos, login=True)

        valor = secrets.token_urlsafe(32)
        sessao = Sessao(
            id_hash=_hash(valor),
            ldap=campos["ldap"],
            roles=campos["roles"],
            renovar_em=campos["renovar_em"],
            refresh_token=tokens.refresh_token,
            expira_em=agora_ + timedelta(seconds=self.settings.session_ttl_segundos),
        )
        self.session.add(sessao)
        await self.session.commit()
        return valor

    async def obter_usuario(self, valor_do_cookie: str) -> UsuarioAtual | None:
        sessao = await self.session.get(Sessao, _hash(valor_do_cookie))
        if sessao is None:
            return None
        usuario = await self.session.get(Usuario, sessao.ldap)
        if (
            usuario is None
            or not usuario.ativo
            or sessao.expira_em <= agora()
            or (sessao.renovar_em <= agora() and not await self._renovar(sessao))
        ):
            await self.session.delete(sessao)
            await self.session.commit()
            return None
        await self.session.refresh(usuario)  # _renovar pode ter atualizado nome/agência
        return UsuarioAtual(
            ldap=usuario.ldap, nome=usuario.nome, agencia=usuario.agencia, roles=tuple(sessao.roles)
        )

    async def encerrar(self, valor_do_cookie: str) -> None:
        await self.session.execute(delete(Sessao).where(Sessao.id_hash == _hash(valor_do_cookie)))
        await self.session.commit()

    async def _renovar(self, sessao: Sessao) -> bool:
        """O id_token expirou: pergunta de novo ao Entra (pega mudança de perfil/desligamento)."""
        if not sessao.refresh_token:
            return False
        try:
            tokens = await self.entra.renovar(sessao.refresh_token)
            claims = await self.entra.validar_id_token(tokens.id_token, nonce=None)
            campos = self._campos(claims)
        except FalhaDeAutenticacao:
            return False
        if campos["ldap"] != sessao.ldap:
            return False
        await self._upsert_usuario(campos, login=False)
        sessao.roles = campos["roles"]
        sessao.renovar_em = campos["renovar_em"]
        sessao.refresh_token = tokens.refresh_token or sessao.refresh_token  # Entra real rotaciona
        await self.session.commit()
        return True

    async def _upsert_usuario(self, campos: dict[str, Any], *, login: bool) -> None:
        """Cria ou atualiza o diretório. Nunca mexe em `ativo` nem em `origem`."""
        dados = {k: campos[k] for k in ("oid", "nome", "email", "agencia")}
        atualizar = dict(dados)
        if login:
            atualizar["ultimo_login"] = agora()
        stmt = (
            insert(Usuario)
            .values(ldap=campos["ldap"], ultimo_login=agora() if login else None, **dados)
            .on_conflict_do_update(index_elements=[Usuario.ldap], set_=atualizar)
            .returning(Usuario.ativo)
        )
        if not (await self.session.execute(stmt)).scalar_one():
            await self.session.rollback()
            raise FalhaDeAutenticacao("usuário desativado")

    @staticmethod
    def _campos(claims: dict[str, Any]) -> dict[str, Any]:
        ldap = claims.get("ldap")
        if not ldap:
            raise FalhaDeAutenticacao("id_token sem a claim 'ldap'")
        return {
            "ldap": ldap,
            "oid": claims.get("oid"),
            "nome": claims.get("name", ldap),
            "email": claims.get("email"),
            "agencia": claims.get("agencia"),
            "roles": list(claims.get("roles", [])),
            "renovar_em": _de_epoch(claims["exp"]),
        }
