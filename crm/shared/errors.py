"""Três famílias de erro de negócio. O main.py mapeia cada uma para um status HTTP."""


class NaoEncontrado(Exception):  # 404
    pass


class AcessoNegado(Exception):  # 403
    pass


class RegraDeNegocio(Exception):  # 422
    pass
