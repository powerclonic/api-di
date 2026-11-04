from datetime import date, timedelta

from crm.modules.agenda.contracts import FonteDeAgenda, ItemDeAgenda
from crm.shared.auth import UsuarioAtual
from crm.shared.errors import RegraDeNegocio

MAX_DIAS = 366


class AgendaService:
    """Agrega as fontes registradas (tarefas, visitas, ...). Não conhece nenhuma delas."""

    def __init__(self, fontes: list[FonteDeAgenda], usuario: UsuarioAtual):
        self.fontes = fontes
        self.usuario = usuario

    async def do_periodo(self, inicio: date, fim: date) -> list[ItemDeAgenda]:
        if fim < inicio:
            raise RegraDeNegocio("O fim do período não pode ser anterior ao início")
        if fim - inicio > timedelta(days=MAX_DIAS):
            raise RegraDeNegocio(f"Período máximo de {MAX_DIAS} dias")
        itens: list[ItemDeAgenda] = []
        # Em sequência de propósito: as fontes compartilham a AsyncSession da requisição, que
        # não aceita operações concorrentes (asyncio.gather quebraria).
        for fonte in self.fontes:
            itens += await fonte.itens(self.usuario.ldap, inicio, fim)
        return sorted(itens, key=lambda i: (i.data, i.origem))
