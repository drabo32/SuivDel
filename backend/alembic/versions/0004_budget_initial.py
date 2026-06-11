"""Ajout colonne budget_initial sur evolution

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evolutions",
        sa.Column("budget_initial", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evolutions", "budget_initial")
