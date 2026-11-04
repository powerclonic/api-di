"""Regras de negócio do TarefaService, isoladas: repositório e Core são fakes em memória."""

from datetime import date

import pytest

from crm.clients.core.tarefas import StatusCore
from crm.modules.tarefas.models import StatusTarefa, Tarefa
from crm.modules.tarefas.service import TarefaService
from crm.shared.auth import UsuarioAtual
from crm.shared.errors import AcessoNegado, NaoEncontrado
from tests.fakes import FakeCore, FakeTarefaRepository

ANA = UsuarioAtual(ldap="ana", nome="Ana")
BIA = UsuarioAtual(ldap="bia", nome="Bia")
CAIO = UsuarioAtual(ldap="caio", nome="Caio")


def _tarefa(solicitante="ana", responsavel="ana", **kw) -> Tarefa:
    return Tarefa(
        titulo="Ligar",
        cpf_cnpj="123",
        solicitante_ldap=solicitante,
        responsavel_ldap=responsavel,
        prazo=kw.pop("prazo", None),
        status=kw.pop("status", StatusTarefa.ABERTA),
        **kw,
    )


def _service(usuario, *tarefas):
    repo, core = FakeTarefaRepository(*tarefas), FakeCore()
    return TarefaService(repo, core, usuario), repo, core


async def test_criar_sem_responsavel_atribui_a_si_mesmo():
    service, repo, core = _service(ANA)
    tarefa = await service.criar("Ligar", "123", date(2026, 12, 1), None)

    assert tarefa.solicitante_ldap == tarefa.responsavel_ldap == "ana"
    assert repo.commits == 1


async def test_criar_envia_ao_core_com_o_responsavel_como_owner():
    service, _, core = _service(ANA)
    tarefa = await service.criar("Ligar", "123", None, "bia")

    (enviada,) = core.registradas
    assert enviada.source_external_id == str(tarefa.id)
    assert enviada.owner == "bia"
    assert enviada.suid == "123"


async def test_delegar_so_pelo_solicitante():
    t = _tarefa(solicitante="ana", responsavel="bia")
    service, repo, _ = _service(BIA, t)  # bia participa, mas não criou

    with pytest.raises(AcessoNegado):
        await service.delegar(t.id, "caio")
    assert t.responsavel_ldap == "bia"
    assert repo.commits == 0


async def test_delegar_troca_o_responsavel():
    t = _tarefa()
    service, repo, _ = _service(ANA, t)

    await service.delegar(t.id, "caio")

    assert t.responsavel_ldap == "caio"
    assert t.delegada
    assert repo.commits == 1


async def test_mudar_status_so_pelo_responsavel():
    t = _tarefa(solicitante="ana", responsavel="bia")
    service, _, core = _service(ANA, t)  # ana pediu, bia executa

    with pytest.raises(AcessoNegado):
        await service.mudar_status(t.id, StatusTarefa.CONCLUIDA)
    assert t.status == StatusTarefa.ABERTA
    assert core.edicoes == []


async def test_mudar_status_avisa_o_core():
    t = _tarefa()
    service, _, core = _service(ANA, t)

    await service.mudar_status(t.id, StatusTarefa.CONCLUIDA)

    assert core.edicoes == [(str(t.id), "123", StatusCore.COMPLETED, None)]


async def test_voltar_para_aberta_nao_chama_o_core():
    t = _tarefa(status=StatusTarefa.EM_ANDAMENTO)
    service, repo, core = _service(ANA, t)

    await service.mudar_status(t.id, StatusTarefa.ABERTA)

    assert t.status == StatusTarefa.ABERTA
    assert core.edicoes == []  # o PATCH do Core não aceita voltar para OPEN
    assert repo.commits == 1


async def test_tarefa_inexistente():
    from uuid import uuid4

    service, _, _ = _service(ANA)
    with pytest.raises(NaoEncontrado):
        await service.delegar(uuid4(), "bia")


async def test_quem_nao_participa_nao_acessa():
    t = _tarefa(solicitante="ana", responsavel="bia")
    service, _, _ = _service(CAIO, t)

    with pytest.raises(AcessoNegado):
        await service.mudar_status(t.id, StatusTarefa.CONCLUIDA)


async def test_listar_separa_minhas_e_acompanhando():
    minha = _tarefa(solicitante="ana", responsavel="ana")
    delegada = _tarefa(solicitante="ana", responsavel="bia")
    service, _, _ = _service(ANA, minha, delegada)

    assert await service.listar("minhas") == [minha]
    assert await service.listar("acompanhando") == [delegada]
