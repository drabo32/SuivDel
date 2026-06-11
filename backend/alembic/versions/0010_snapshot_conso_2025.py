"""Ajout conso_2025 dans snapshots_atterrissage

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("snapshots_atterrissage", sa.Column("conso_2025", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("snapshots_atterrissage", "conso_2025")
