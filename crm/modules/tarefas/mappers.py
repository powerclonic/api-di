from crm.clients.core.tarefas import StatusCore
from crm.clients.core.tarefas import Tarefa as TarefaCore
from crm.modules.tarefas.models import StatusTarefa, Tarefa

_STATUS = {
    StatusTarefa.ABERTA: StatusCore.OPEN,
    StatusTarefa.EM_ANDAMENTO: StatusCore.IN_PROGRESS,
    StatusTarefa.CONCLUIDA: StatusCore.COMPLETED,
}


def status_para_api(status: StatusTarefa) -> StatusCore:
    return _STATUS[status]


def para_api(tarefa: Tarefa) -> TarefaCore:
    return TarefaCore(
        source_external_id=str(tarefa.id),
        suid=tarefa.cpf_cnpj,
        type="tarefa",
        title=tarefa.titulo,
        owner=tarefa.responsavel_ldap,
        plan_end=tarefa.prazo,
        status=status_para_api(tarefa.status),
    )
