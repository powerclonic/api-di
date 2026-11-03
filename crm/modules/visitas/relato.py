from pydantic import BaseModel


class RelatoEstruturado(BaseModel):
    resumo: str
    pontos_de_atencao: list[str] = []
    proximos_passos: list[str] = []
