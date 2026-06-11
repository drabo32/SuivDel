"""Ajout table rafs_hors_evolutions

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rafs_hors_evolutions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("time_niv2", sa.String(100), nullable=False),
        sa.Column("nom_tache", sa.String(500), nullable=False, server_default=""),
        sa.Column("raf", sa.Float(), nullable=False, server_default="0"),
        sa.UniqueConstraint("time_niv2", "nom_tache", name="uq_raf_hors_evol"),
    )


def downgrade() -> None:
    op.drop_table("rafs_hors_evolutions")
