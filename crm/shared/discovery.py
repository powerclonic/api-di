"""Autodescoberta por convenção sobre `crm/modules/**`.

Um módulo (ou submódulo dele) novo = pasta nova com os arquivos da convenção; nada central muda:
  provider.py -> subclasses de `Provider` (DI)
  router.py   -> variável `router` (APIRouter)
  models.py   -> importado só para registrar as tabelas no `Base.metadata` (Alembic)
Pastas sem o arquivo são ignoradas (ex.: carteira, que só repassa o datalake)."""

import inspect
import pkgutil
from importlib import import_module
from types import ModuleType

from dishka import Provider
from fastapi import APIRouter

PACOTE = "crm.modules"


def _importar(arquivo: str, pacote: str = PACOTE) -> list[ModuleType]:
    raiz = import_module(pacote)
    achados: list[ModuleType] = []
    for info in pkgutil.walk_packages(raiz.__path__, prefix=f"{pacote}."):
        if info.name.rpartition(".")[2] != arquivo:
            continue
        achados.append(import_module(info.name))
    return achados


def discover_providers(pacote: str = PACOTE) -> list[Provider]:
    return [
        cls()
        for mod in _importar("provider", pacote)
        for cls in vars(mod).values()
        if inspect.isclass(cls) and issubclass(cls, Provider) and cls.__module__ == mod.__name__
    ]


def discover_routers(pacote: str = PACOTE) -> list[APIRouter]:
    return [mod.router for mod in _importar("router", pacote)]


def discover_models(pacote: str = PACOTE) -> None:
    _importar("models", pacote)
