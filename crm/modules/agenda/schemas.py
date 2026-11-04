from datetime import date

from pydantic import BaseModel, ConfigDict


class ItemDeAgendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    origem: str
    id: str
    titulo: str
    data: date
    cpf_cnpj: str | None
