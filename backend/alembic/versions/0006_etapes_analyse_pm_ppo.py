"""Ajout étapes Analyse PM et Analyse PPO dans le cycle de vie

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE ne peut pas s'exécuter dans un bloc transactionnel
    # → on sort de la transaction, on ajoute les valeurs, on recommence
    conn = op.get_bind()
    conn.execute(sa.text("COMMIT"))
    conn.execute(sa.text(
        "ALTER TYPE numeroetape ADD VALUE IF NOT EXISTS 'Analyse PM' BEFORE 'Analyse PO'"
    ))
    conn.execute(sa.text(
        "ALTER TYPE numeroetape ADD VALUE IF NOT EXISTS 'Analyse PPO' AFTER 'Analyse PO'"
    ))
    conn.execute(sa.text("BEGIN"))

    # Créer les deux nouvelles étapes pour toutes les évolutions qui ne les ont pas
    conn.execute(sa.text("""
        INSERT INTO etapes_cycle_vie
            (evolution_code, etape, statut, pourcentage_avancement, version_verrou, date_modification)
        SELECT e.code,
               'Analyse PM'::numeroetape,
               'À faire'::statutetape,
               0, 0, NOW()
        FROM evolutions e
        WHERE NOT EXISTS (
            SELECT 1 FROM etapes_cycle_vie ecv
            WHERE ecv.evolution_code = e.code
              AND ecv.etape = 'Analyse PM'::numeroetape
        )
    """))

    conn.execute(sa.text("""
        INSERT INTO etapes_cycle_vie
            (evolution_code, etape, statut, pourcentage_avancement, version_verrou, date_modification)
        SELECT e.code,
               'Analyse PPO'::numeroetape,
               'À faire'::statutetape,
               0, 0, NOW()
        FROM evolutions e
        WHERE NOT EXISTS (
            SELECT 1 FROM etapes_cycle_vie ecv
            WHERE ecv.evolution_code = e.code
              AND ecv.etape = 'Analyse PPO'::numeroetape
        )
    """))


def downgrade() -> None:
    # PostgreSQL ne supporte pas la suppression de valeurs d'enum
    # → on supprime juste les lignes d'étapes correspondantes
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM etapes_cycle_vie WHERE etape IN ('Analyse PM', 'Analyse PPO')"
    ))
