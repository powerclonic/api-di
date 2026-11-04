"""visitas

Revision ID: c7e9a1b3d5f2
Revises:
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7e9a1b3d5f2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = ("visitas",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visitas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("gerente_ldap", sa.String(), nullable=False),
        sa.Column("cpf_cnpj", sa.String(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("relato_bruto", sa.String(), nullable=False),
        sa.Column("relato", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("rascunho", "revisao", "confirmada", name="statusvisita", native_enum=False, length=20),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_visitas_gerente_ldap"), "visitas", ["gerente_ldap"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_visitas_gerente_ldap"), table_name="visitas")
    op.drop_table("visitas")
