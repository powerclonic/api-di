from datetime import date

from crm.modules.agenda.contracts import ItemDeAgenda
from crm.modules.visitas.repository import VisitaRepository


class FonteVisitas:
    """Implementa `FonteDeAgenda`: visitas do gerente, pela data."""

    def __init__(self, repository: VisitaRepository):
        self.repository = repository

    async def itens(self, ldap: str, inicio: date, fim: date) -> list[ItemDeAgenda]:
        visitas = await self.repository.do_gerente_no_periodo(ldap, inicio, fim)
        return [
            ItemDeAgenda(
                origem="visita",
                id=str(v.id),
                titulo=f"Visita ({v.status.value})",
                data=v.data,
                cpf_cnpj=v.cpf_cnpj,
            )
            for v in visitas
        ]
