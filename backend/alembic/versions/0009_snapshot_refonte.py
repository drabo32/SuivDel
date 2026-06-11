"""Refonte snapshots — ajout budget/macro_chiffrage/chiffrage_edition, suppression date_fin_estimee, suppression contrainte unique

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_snapshot", "snapshots_atterrissage", type_="unique")
    op.drop_column("snapshots_atterrissage", "date_fin_estimee")
    op.add_column("snapshots_atterrissage", sa.Column("budget", sa.Float(), nullable=True))
    op.add_column("snapshots_atterrissage", sa.Column("macro_chiffrage", sa.Float(), nullable=True))
    op.add_column("snapshots_atterrissage", sa.Column("chiffrage_edition", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("snapshots_atterrissage", "chiffrage_edition")
    op.drop_column("snapshots_atterrissage", "macro_chiffrage")
    op.drop_column("snapshots_atterrissage", "budget")
    op.add_column("snapshots_atterrissage", sa.Column("date_fin_estimee", sa.Date(), nullable=True))
    op.create_unique_constraint("uq_snapshot", "snapshots_atterrissage", ["evolution_code", "annee", "mois"])
