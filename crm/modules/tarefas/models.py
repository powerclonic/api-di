from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from crm.shared.db import Base


class StatusTarefa(StrEnum):
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"


class Tarefa(Base):
    __tablename__ = "tarefas"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)  # = sourceExternalId
    titulo: Mapped[str]
    solicitante_ldap: Mapped[str] = mapped_column(index=True)
    responsavel_ldap: Mapped[str] = mapped_column(index=True)
    prazo: Mapped[date | None]
    status: Mapped[StatusTarefa] = mapped_column(
        Enum(StatusTarefa, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=StatusTarefa.ABERTA,
    )

    @property
    def delegada(self) -> bool:
        return self.solicitante_ldap != self.responsavel_ldap

    def delegar(self, para_ldap: str) -> None:
        self.responsavel_ldap = para_ldap  # para o solicitante, passa a ser "acompanhamento"
