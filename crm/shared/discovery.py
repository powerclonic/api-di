"""Autodiscovery dos providers dos módulos.

Todo `crm/modules/<nome>/provider.py` é importado e cada subclasse de `Provider` definida nele
vira parte do container. Módulo novo = pasta nova com um provider.py; o container não muda.
Módulos sem provider.py (ex.: carteira, que só repassa o datalake) são ignorados."""

import inspect
import pkgutil
from importlib import import_module

from dishka import Provider


def discover_providers(pacote: str = "crm.modules") -> list[Provider]:
    providers: list[Provider] = []
    for modulo in pkgutil.iter_modules(import_module(pacote).__path__):
        nome = f"{pacote}.{modulo.name}.provider"
        try:
            mod = import_module(nome)
        except ModuleNotFoundError as exc:
            if exc.name == nome:  # o módulo não tem provider.py; qualquer outro erro é bug real
                continue
            raise
        providers += [
            cls()
            for cls in vars(mod).values()
            if inspect.isclass(cls) and issubclass(cls, Provider) and cls.__module__ == nome
        ]
    return providers
