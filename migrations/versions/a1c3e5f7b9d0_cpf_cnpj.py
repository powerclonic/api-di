"""cpf_cnpj do associado em tarefas (novo) e visitas (renomeia associado_id); vira o suid no Core

Revision ID: a1c3e5f7b9d0
Revises: 42362fe2eb60
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c3e5f7b9d0"
down_revision: Union[str, Sequence[str], None] = "42362fe2eb60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default só para preencher linhas antigas; o app sempre informa o valor.
    op.add_column("tarefas", sa.Column("cpf_cnpj", sa.String(), nullable=False, server_default=""))
    op.alter_column("tarefas", "cpf_cnpj", server_default=None)
    op.alter_column("visitas", "associado_id", new_column_name="cpf_cnpj")


def downgrade() -> None:
    op.alter_column("visitas", "cpf_cnpj", new_column_name="associado_id")
    op.drop_column("tarefas", "cpf_cnpj")
