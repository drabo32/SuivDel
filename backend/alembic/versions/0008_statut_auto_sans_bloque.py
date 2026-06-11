"""Suppression statut Bloqué + statut entièrement dérivé du pourcentage

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # La colonne statut peut être en text ou en statutetape selon l'état de la DB.
    # On travaille en text pour être robuste dans les deux cas.

    # 1. Passer la colonne en text si ce n'est pas déjà le cas
    conn.execute(sa.text("COMMIT"))
    conn.execute(sa.text(
        "ALTER TABLE etapes_cycle_vie "
        "ALTER COLUMN statut TYPE text USING statut::text"
    ))

    # 2. Recalculer toutes les lignes selon la règle métier (traite aussi Bloqué)
    conn.execute(sa.text("""
        UPDATE etapes_cycle_vie
        SET statut = CASE
            WHEN pourcentage_avancement = 0   THEN 'À faire'
            WHEN pourcentage_avancement = 100 THEN 'Terminé'
            ELSE 'En cours'
        END
    """))

    # 3. Supprimer la valeur DEFAULT qui référence l'ancien type, puis supprimer le type
    conn.execute(sa.text(
        "ALTER TABLE etapes_cycle_vie ALTER COLUMN statut DROP DEFAULT"
    ))
    conn.execute(sa.text("DROP TYPE IF EXISTS statutetape CASCADE"))
    conn.execute(sa.text(
        "CREATE TYPE statutetape AS ENUM ('À faire', 'En cours', 'Terminé')"
    ))

    # 4. Repasser la colonne sur le nouveau type + restaurer le DEFAULT
    conn.execute(sa.text(
        "ALTER TABLE etapes_cycle_vie "
        "ALTER COLUMN statut TYPE statutetape USING statut::statutetape"
    ))
    conn.execute(sa.text(
        "ALTER TABLE etapes_cycle_vie "
        "ALTER COLUMN statut SET DEFAULT 'À faire'::statutetape"
    ))
    conn.execute(sa.text("BEGIN"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("COMMIT"))
    conn.execute(sa.text(
        "ALTER TABLE etapes_cycle_vie ALTER COLUMN statut TYPE text"
    ))
    conn.execute(sa.text("DROP TYPE statutetape"))
    conn.execute(sa.text(
        "CREATE TYPE statutetape AS ENUM ('À faire', 'En cours', 'Terminé', 'Bloqué')"
    ))
    conn.execute(sa.text(
        "ALTER TABLE etapes_cycle_vie ALTER COLUMN statut TYPE statutetape "
        "USING statut::statutetape"
    ))
    conn.execute(sa.text("BEGIN"))
