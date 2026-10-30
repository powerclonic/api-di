"""IA: texto livre -> relato estruturado + oportunidades.

Os schemas abaixo são o formato de saída da IA (no real, o que se passa para
`llm.with_structured_output(RelatoEstruturado)`). Só este arquivo conhece o LangChain."""

from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Oportunidade(BaseModel):
    titulo: str
    descricao: str
    id: UUID = Field(default_factory=uuid4)  # vira o sourceExternalId no Core


class RelatoEstruturado(BaseModel):
    resumo: str
    pontos_de_atencao: list[str] = []
    proximos_passos: list[str] = []
    oportunidades: list[Oportunidade] = []


class IaGateway(Protocol):
    async def estruturar_relato(self, texto: str) -> RelatoEstruturado: ...


# --- Implementações ----------------------------------------------------------
# IaLangChain(IaGateway): AI Foundry via LangChain  <- a implementação real
_PALAVRAS = {
    "financiamento": "Financiamento imobiliário",
    "seguro": "Seguro",
    "consórcio": "Consórcio",
    "investimento": "Investimentos",
}


class IaFake(IaGateway):
    """Procura palavras-chave. Serve para dev e testes, sem gastar chamadas."""

    async def estruturar_relato(self, texto: str) -> RelatoEstruturado:
        baixo = texto.lower()
        return RelatoEstruturado(
            resumo=texto.strip().split(".")[0],
            proximos_passos=["Retornar o contato em 7 dias"],
            oportunidades=[
                Oportunidade(titulo=titulo, descricao=f"Mencionado no relato: '{palavra}'")
                for palavra, titulo in _PALAVRAS.items()
                if palavra in baixo
            ],
        )
