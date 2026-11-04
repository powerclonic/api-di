from crm.clients.core.tarefas import Tarefa as TarefaCore
from crm.modules.agencia.service import AgenciaService
from tests.fakes import FakeCore


async def test_devolve_as_tarefas_de_todos_da_agencia_sem_filtrar_por_owner():
    core = FakeCore(
        TarefaCore(source_external_id="1", suid="123", title="Ligar", owner="ana"),
        TarefaCore(source_external_id="2", suid="456", title="Visitar", owner="bia"),
    )
    resultado = await AgenciaService(core).tarefas_da_agencia()
    assert [t.owner for t in resultado] == ["ana", "bia"]
    assert core.buscas == [{}]  # a agência vem do client, não de parâmetro
