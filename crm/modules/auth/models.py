from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from crm.shared.db import Base


def agora() -> datetime:
    return datetime.now(UTC)


class Usuario(Base):
    """Diretório local. O Entra continua sendo a fonte da verdade: isto é a última versão que
    ele nos disse (no login, hoje; via SCIM, se um dia vier). `ativo` é nosso: só um
    deprovisionamento o desliga. `roles` não ficam aqui, vêm do token a cada renovação."""

    __tablename__ = "usuarios"

    ldap: Mapped[str] = mapped_column(primary_key=True)
    oid: Mapped[str | None]
    nome: Mapped[str]
    email: Mapped[str | None]
    agencia: Mapped[str | None] = mapped_column(index=True)
    ativo: Mapped[bool] = mapped_column(default=True)
    origem: Mapped[str] = mapped_column(default="login")  # 'login' | 'scim'
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Sessao(Base):
    """Sessão do BFF. O cookie guarda um valor aleatório; aqui fica só o SHA-256 dele,
    então um vazamento do banco não entrega sessões utilizáveis."""

    __tablename__ = "sessoes"

    id_hash: Mapped[str] = mapped_column(primary_key=True)
    ldap: Mapped[str] = mapped_column(ForeignKey("usuarios.ldap", ondelete="CASCADE"), index=True)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    refresh_token: Mapped[str | None]  # TODO: cifrar em repouso antes de produção
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    renovar_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # exp do id_token
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # teto absoluto
