"""Ajout table historique_diff_release

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "historique_diff_release",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_import", sa.Integer(), sa.ForeignKey("historique_imports.id"), nullable=True),
        sa.Column("date_import", sa.DateTime(), nullable=False),
        sa.Column("code_release", sa.String(50), nullable=False),
        sa.Column("evolution_code", sa.String(50), nullable=False),
        sa.Column("libelle_evolution", sa.Text(), nullable=True),
        sa.Column("type_diff", sa.String(20), nullable=False),
        sa.Column("ancienne_valeur", sa.String(200), nullable=True),
        sa.Column("nouvelle_valeur", sa.String(200), nullable=True),
    )
    op.create_index("ix_hdr_code_release", "historique_diff_release", ["code_release"])
    op.create_index("ix_hdr_id_import", "historique_diff_release", ["id_import"])


def downgrade() -> None:
    op.drop_index("ix_hdr_id_import", "historique_diff_release")
    op.drop_index("ix_hdr_code_release", "historique_diff_release")
    op.drop_table("historique_diff_release")
