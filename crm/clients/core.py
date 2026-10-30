"""Core (CRM sistêmico): tarefas (visita é tarefa com type='visita') e oportunidades.

Esta é a nossa camada anticorrupção. O CoreGateway fala a linguagem do NOSSO app
(registrar_visita, registrar_tarefa); cada implementação traduz para o que o Core
entende (payload da API, fluxo do RPA...). Trocar RPA por API = uma classe nova e uma
linha no container.

O id da visita, da tarefa e de cada oportunidade é gerado por nós e enviado como
sourceExternalId: o Core reconhece o mesmo id, então o retry não duplica."""

from typing import ClassVar, Protocol

from crm.modules.tarefas.models import Tarefa
from crm.modules.visitas.models import Visita
from crm.shared.auth import UsuarioAtual


class CoreGateway(Protocol):
    async def registrar_visita(self, visita: Visita) -> None: ...

    async def registrar_tarefa(self, tarefa: Tarefa) -> None: ...  # cria ou edita


# --- Implementações ----------------------------------------------------------
# CoreApi(CoreGateway): httpx + credencial do usuário impessoal  <- a real
# CoreRpa(CoreGateway): o fluxo atual, se ainda for preciso
class CoreFake(CoreGateway):
    """Guarda em memória e imprime. Mesmo shape de payload que a API real terá."""

    registros: ClassVar[dict[str, dict]] = {}

    def __init__(self, usuario: UsuarioAtual):
        self.usuario = usuario  # o LDAP vai em toda chamada ao Core

    async def registrar_visita(self, visita: Visita) -> None:
        relato = visita.relato_estruturado
        assert relato is not None
        self._upsert(
            "tarefas",
            {
                "sourceExternalId": str(visita.id),
                "type": "visita",
                "title": f"Visita ao associado {visita.associado_id}",
                "date": visita.data.isoformat(),
                "description": f"{relato.resumo}\nPróximos passos: {'; '.join(relato.proximos_passos)}",
            },
        )
        for oportunidade in relato.oportunidades:
            self._upsert(
                "oportunidades",
                {
                    "sourceExternalId": str(oportunidade.id),
                    "title": oportunidade.titulo,
                    "description": oportunidade.descricao,
                },
            )

    async def registrar_tarefa(self, tarefa: Tarefa) -> None:
        self._upsert(
            "tarefas",
            {
                "sourceExternalId": str(tarefa.id),
                "type": "tarefa",
                "title": tarefa.titulo,
                "status": tarefa.status.value,
                "requester": tarefa.solicitante_ldap,
                "assignee": tarefa.responsavel_ldap,
            },
        )

    def _upsert(self, recurso: str, payload: dict) -> None:
        chave = payload["sourceExternalId"]
        acao = "editou" if chave in self.registros else "criou"
        self.registros[chave] = {"recurso": recurso, "ldap": self.usuario.ldap, **payload}
        print(f"  [core] {acao} {recurso} {chave[:8]} (ldap={self.usuario.ldap})")
