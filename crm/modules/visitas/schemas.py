from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from crm.clients.ia import RelatoEstruturado
from crm.modules.visitas.models import StatusVisita


class NovaVisita(BaseModel):
    associado_id: str
    data: date
    relato: str  # texto digitado; áudio e imagem entram depois, gerando este mesmo texto


class VisitaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    associado_id: str
    data: date
    status: StatusVisita
    relato_bruto: str
    relato: RelatoEstruturado | None
