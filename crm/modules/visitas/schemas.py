from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from crm.modules.visitas.models import StatusVisita
from crm.modules.visitas.relato import RelatoEstruturado


class NovaVisita(BaseModel):
    cpf_cnpj: str
    data: date
    relato: str  # texto digitado; áudio e imagem entram depois, gerando este mesmo texto


class VisitaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cpf_cnpj: str
    data: date
    status: StatusVisita
    relato_bruto: str
    relato: RelatoEstruturado | None
