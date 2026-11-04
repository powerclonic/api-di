from datetime import date
from uuid import UUID

from crm.clients.core import CoreGateway
from crm.modules.agenda.visitas.mappers import para_api
from crm.modules.agenda.visitas.models import Visita
from crm.modules.agenda.visitas.relato import RelatoEstruturado
from crm.modules.agenda.visitas.repository import VisitaRepository
from crm.shared.auth import UsuarioAtual
from crm.shared.errors import AcessoNegado, NaoEncontrado


class VisitaService:
    def __init__(
        self,
        repository: VisitaRepository,
        core: CoreGateway,
        usuario: UsuarioAtual,
    ):
        self.repository = repository
        self.core = core
        self.usuario = usuario

    async def registrar(self, cpf_cnpj: str, data: date, relato_bruto: str) -> Visita:
        visita = Visita(
            gerente_ldap=self.usuario.ldap,
            cpf_cnpj=cpf_cnpj,
            data=data,
            relato_bruto=relato_bruto,
        )
        self.repository.adicionar(visita)
        await self.repository.commit()
        return visita

    async def listar(self) -> list[Visita]:
        return await self.repository.listar_do_gerente(self.usuario.ldap)

    async def obter(self, visita_id: UUID) -> Visita:
        visita = await self.repository.obter(visita_id)
        if visita is None:
            raise NaoEncontrado(f"Visita {visita_id} não encontrada")
        if visita.gerente_ldap != self.usuario.ldap:
            raise AcessoNegado("Esta visita pertence a outro gerente")
        return visita

    async def editar_relato(self, visita_id: UUID, relato: RelatoEstruturado) -> Visita:
        visita = await self.obter(visita_id)
        visita.definir_relato(relato)
        await self.repository.commit()
        return visita

    async def confirmar(self, visita_id: UUID) -> Visita:
        visita = await self.obter(visita_id)
        visita.confirmar()
        # Core antes do commit: se falhar, nada é salvo e o gerente tenta de novo. A API cria e
        # edita em rotas distintas, então o retry consulta antes (o Core pode já ter recebido).
        if not await self.core.buscar(source_external_id=str(visita.id)):
            await self.core.registrar(para_api(visita))
        await self.repository.commit()
        return visita
