from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from crm.modules.agenda.tarefas.models import StatusTarefa


class NovaTarefa(BaseModel):
    titulo: str
    cpf_cnpj: str
    prazo: date | None = None
    responsavel_ldap: str | None = None  # vazio = para mim; preenchido = já nasce delegada


class Delegacao(BaseModel):
    responsavel_ldap: str


class MudancaDeStatus(BaseModel):
    status: StatusTarefa


class TarefaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    cpf_cnpj: str
    solicitante_ldap: str
    responsavel_ldap: str
    prazo: date | None
    status: StatusTarefa
    delegada: bool
