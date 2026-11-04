"""Contrato público da agenda: a ÚNICA parte de `agenda` que outros módulos podem importar.

A agenda não conhece quem a alimenta. Cada módulo com algo que cai na agenda do gerente
(tarefas, visitas, aniversários...) implementa `FonteDeAgenda` no próprio provider; a agenda
agrega as fontes registradas. Fonte nova = código só no módulo dela."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class ItemDeAgenda:
    origem: str  # identifica a fonte: "tarefa", "visita", "aniversario"...
    id: str  # id do registro na fonte (string: a agenda não presume o tipo)
    titulo: str
    data: date
    cpf_cnpj: str | None = None  # associado a que o item se refere, se houver


class FonteDeAgenda(Protocol):
    async def itens(self, ldap: str, inicio: date, fim: date) -> list[ItemDeAgenda]:
        """Itens do gerente `ldap` com data em [inicio, fim]."""
        ...
