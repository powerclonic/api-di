"""APIs internas (datalake) feitas sob medida para o CRM. Só leitura.

Sempre em nome do usuário atual: a implementação recebe o UsuarioAtual e manda o LDAP dele.
O Protocol serve de rascunho do contrato para o time do datalake."""

from datetime import date
from typing import ClassVar, Protocol

from pydantic import BaseModel

from crm.shared.auth import UsuarioAtual


class Associado(BaseModel):
    id: str
    nome: str
    nascimento: date


class DatalakeGateway(Protocol):
    async def carteira(self) -> list[Associado]: ...

    async def aniversariantes(self, mes: int) -> list[Associado]: ...

    async def colaboradores_da_agencia(self) -> list[str]:
        """LDAPs de quem trabalha na mesma agência do usuário."""
        ...


# --- Implementações ----------------------------------------------------------
# DatalakeApi(DatalakeGateway): httpx nas APIs internas  <- a implementação real
class DatalakeFake(DatalakeGateway):
    _CARTEIRAS: ClassVar[dict[str, list[Associado]]] = {
        "gerente1": [
            Associado(id="A1", nome="Maria Silva", nascimento=date(1980, 10, 30)),
            Associado(id="A2", nome="João Souza", nascimento=date(1975, 11, 2)),
            Associado(id="A3", nome="Ana Lima", nascimento=date(1990, 10, 5)),
        ],
    }
    _AGENCIA_001: ClassVar[list[str]] = ["gerente1", "assistente1", "assistente2"]

    def __init__(self, usuario: UsuarioAtual):
        self.usuario = usuario

    async def carteira(self) -> list[Associado]:
        return self._CARTEIRAS.get(self.usuario.ldap, [])

    async def aniversariantes(self, mes: int) -> list[Associado]:
        return [a for a in await self.carteira() if a.nascimento.month == mes]

    async def colaboradores_da_agencia(self) -> list[str]:
        return self._AGENCIA_001 if self.usuario.ldap in self._AGENCIA_001 else []
