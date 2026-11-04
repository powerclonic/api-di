"""cpf_cnpj do associado em tarefas; vira o suid no Core

Revision ID: a1c3e5f7b9d0
Revises: ea05c6356fc9
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c3e5f7b9d0"
down_revision: Union[str, Sequence[str], None] = "ea05c6356fc9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default só para preencher linhas antigas; o app sempre informa o valor.
    op.add_column("tarefas", sa.Column("cpf_cnpj", sa.String(), nullable=False, server_default=""))
    op.alter_column("tarefas", "cpf_cnpj", server_default=None)


def downgrade() -> None:
    op.drop_column("tarefas", "cpf_cnpj")
