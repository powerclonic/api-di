from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column

from crm.modules.agenda.visitas.relato import RelatoEstruturado
from crm.shared.db import Base
from crm.shared.errors import RegraDeNegocio


class StatusVisita(StrEnum):
    RASCUNHO = "rascunho"
    REVISAO = "revisao"  # a IA estruturou; o gerente precisa revisar
    CONFIRMADA = "confirmada"  # já registrada no Core


class Visita(Base):
    __tablename__ = "visitas"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)  # = sourceExternalId
    gerente_ldap: Mapped[str] = mapped_column(index=True)
    cpf_cnpj: Mapped[str]
    data: Mapped[date]
    relato_bruto: Mapped[str]
    relato: Mapped[dict | None] = mapped_column(JSON)  # RelatoEstruturado serializado
    status: Mapped[StatusVisita] = mapped_column(
        Enum(StatusVisita, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=StatusVisita.RASCUNHO,
    )

    @property
    def relato_estruturado(self) -> RelatoEstruturado | None:
        return RelatoEstruturado.model_validate(self.relato) if self.relato else None

    def definir_relato(self, relato: RelatoEstruturado) -> None:
        if self.status == StatusVisita.CONFIRMADA:
            raise RegraDeNegocio("Visita confirmada não pode ser editada")
        self.relato = relato.model_dump(mode="json")
        self.status = StatusVisita.REVISAO

    def confirmar(self) -> None:
        if self.status != StatusVisita.REVISAO:
            raise RegraDeNegocio("Só é possível confirmar uma visita em revisão")
        self.status = StatusVisita.CONFIRMADA
