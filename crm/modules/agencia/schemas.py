from datetime import date

from pydantic import BaseModel, ConfigDict

from crm.clients.core.tarefas import StatusCore


class TarefaAgenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_external_id: str
    suid: str
    title: str
    type: str | None
    description: str | None
    owner: str | None
    plan_end: date | None
    status: StatusCore
