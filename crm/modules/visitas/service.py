from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crm.clients.core import CoreGateway
from crm.clients.ia import IaGateway, RelatoEstruturado
from crm.modules.visitas.models import Visita
from crm.shared.auth import UsuarioAtual
from crm.shared.errors import AcessoNegado, NaoEncontrado


class VisitaService:
    def __init__(
        self,
        session: AsyncSession,
        ia: IaGateway,
        core: CoreGateway,
        usuario: UsuarioAtual,
    ):
        self.session = session
        self.ia = ia
        self.core = core
        self.usuario = usuario

    async def registrar(self, associado_id: str, data: date, relato_bruto: str) -> Visita:
        visita = Visita(
            gerente_ldap=self.usuario.ldap,
            associado_id=associado_id,
            data=data,
            relato_bruto=relato_bruto,
        )
        visita.definir_relato(await self.ia.estruturar_relato(relato_bruto))  # -> revisão
        self.session.add(visita)
        await self.session.commit()
        return visita

    async def listar(self) -> list[Visita]:
        consulta = (
            select(Visita)
            .where(Visita.gerente_ldap == self.usuario.ldap)
            .order_by(Visita.data.desc())
        )
        return list(await self.session.scalars(consulta))

    async def obter(self, visita_id: UUID) -> Visita:
        visita = await self.session.get(Visita, visita_id)
        if visita is None:
            raise NaoEncontrado(f"Visita {visita_id} não encontrada")
        if visita.gerente_ldap != self.usuario.ldap:
            raise AcessoNegado("Esta visita pertence a outro gerente")
        return visita

    async def editar_relato(self, visita_id: UUID, relato: RelatoEstruturado) -> Visita:
        visita = await self.obter(visita_id)
        visita.definir_relato(relato)
        await self.session.commit()
        return visita

    async def confirmar(self, visita_id: UUID) -> Visita:
        visita = await self.obter(visita_id)
        visita.confirmar()
        # Core antes do commit: se falhar, nada é salvo e o gerente tenta de novo.
        # O retry é seguro porque o Core recebe o mesmo sourceExternalId.
        await self.core.registrar_visita(visita)
        await self.session.commit()
        return visita
