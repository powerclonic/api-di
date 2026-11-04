from crm.clients.core import Tarefa as TarefaCore
from crm.modules.agenda.visitas.models import Visita


def para_api(visita: Visita) -> TarefaCore:
    """No Core a visita é uma tarefa com type='visita'."""
    relato = visita.relato_estruturado
    assert relato is not None
    return TarefaCore(
        source_external_id=str(visita.id),
        suid=visita.cpf_cnpj,  # CPF/CNPJ do associado
        type="visita",
        title=f"Visita ao associado {visita.cpf_cnpj}",
        description=f"{relato.resumo}\nPróximos passos: {'; '.join(relato.proximos_passos)}",
        owner=visita.gerente_ldap,
        plan_end=visita.data,
    )
