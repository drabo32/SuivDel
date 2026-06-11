"""Suppression colonne budget_initial (fusionnée dans budget)

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("evolutions", "budget_initial")


def downgrade() -> None:
    op.add_column("evolutions", sa.Column("budget_initial", sa.Float(), nullable=True))
