"""Schéma initial complet

Revision ID: 0001
Revises:
Create Date: 2026-05-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Définition des types ENUM réutilisables (create_type=False = ne pas re-créer)
_typeequipe   = ENUM("DEV", "TESTING", name="typeequipe",   create_type=False)
_statutetape  = ENUM("À faire", "En cours", "Terminé", "Bloqué", name="statutetape", create_type=False)
_numeroetape  = ENUM(
    "Analyse PO", "Développement", "Recette interne",
    "Livraison intégration", "Recette Pôle Testing",
    name="numeroetape", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    # Création des types ENUM (checkfirst=True → idempotent)
    ENUM("DEV", "TESTING", name="typeequipe").create(bind, checkfirst=True)
    ENUM("À faire", "En cours", "Terminé", "Bloqué", name="statutetape").create(bind, checkfirst=True)
    ENUM(
        "Analyse PO", "Développement", "Recette interne",
        "Livraison intégration", "Recette Pôle Testing",
        name="numeroetape",
    ).create(bind, checkfirst=True)

    op.create_table(
        "equipes",
        sa.Column("code", sa.String(20), primary_key=True),
        sa.Column("libelle", sa.String(100), nullable=False),
        sa.Column("type_equipe", _typeequipe, nullable=False),
    )

    op.create_table(
        "releases",
        sa.Column("code", sa.String(50), primary_key=True),
        sa.Column("libelle", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("mois", sa.Integer(), nullable=False),
        sa.Column("annee", sa.Integer(), nullable=False),
    )

    op.create_table(
        "workspace_mappings",
        sa.Column("workspace_aha", sa.String(100), primary_key=True),
        sa.Column("code_equipe", sa.String(20), sa.ForeignKey("equipes.code"), nullable=False),
    )

    op.create_table(
        "evolutions",
        sa.Column("code", sa.String(50), primary_key=True),
        sa.Column("libelle", sa.Text(), nullable=False),
        sa.Column("code_equipe", sa.String(20), sa.ForeignKey("equipes.code"), nullable=False),
        sa.Column("code_release", sa.String(50), sa.ForeignKey("releases.code"), nullable=True),
        sa.Column("type_evolution", sa.String(30), nullable=True),
        sa.Column("statut_aha", sa.String(50), nullable=True),
        sa.Column("budget", sa.Float(), nullable=True),
        sa.Column("macro_chiffrage", sa.Float(), nullable=True),
        sa.Column("chiffrage_edition", sa.Float(), nullable=True),
        sa.Column("raf_dev", sa.Float(), nullable=True),
        sa.Column("raf_testing", sa.Float(), nullable=True),
        sa.Column("date_fin_estimee", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.Column("date_import", sa.Date(), nullable=True),
        sa.Column("version_verrou", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "etapes_cycle_vie",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evolution_code", sa.String(50), sa.ForeignKey("evolutions.code"), nullable=False),
        sa.Column("etape", _numeroetape, nullable=False),
        sa.Column("statut", _statutetape, server_default="À faire"),
        sa.Column("date_prevue", sa.Date(), nullable=True),
        sa.Column("date_reelle", sa.Date(), nullable=True),
        sa.Column("pourcentage_avancement", sa.Integer(), server_default="0"),
        sa.Column("responsable", sa.String(100), nullable=True),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("date_modification", sa.DateTime(), nullable=True),
        sa.Column("modifie_par", sa.String(100), nullable=True),
        sa.Column("version_verrou", sa.Integer(), server_default="0"),
        sa.UniqueConstraint("evolution_code", "etape", name="uq_etape_evolution"),
    )

    op.create_table(
        "historique_etapes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evolution_code", sa.String(50), nullable=False),
        sa.Column("etape", sa.String(50), nullable=False),
        sa.Column("champ_modifie", sa.String(50), nullable=False),
        sa.Column("ancienne_valeur", sa.Text(), nullable=True),
        sa.Column("nouvelle_valeur", sa.Text(), nullable=True),
        sa.Column("modifie_par", sa.String(100), nullable=True),
        sa.Column("date_modification", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "ressources",
        sa.Column("matricule", sa.String(20), primary_key=True),
        sa.Column("nom", sa.String(100), nullable=False),
        sa.Column("code_equipe", sa.String(20), sa.ForeignKey("equipes.code"), nullable=True),
        sa.Column("type_equipe", _typeequipe, nullable=True),
    )

    op.create_table(
        "temps_consommes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evolution_code", sa.String(50), sa.ForeignKey("evolutions.code"), nullable=False),
        sa.Column("matricule", sa.String(20), nullable=False),
        sa.Column("nom_ressource", sa.String(100), nullable=True),
        sa.Column("code_equipe", sa.String(20), nullable=True),
        sa.Column("type_equipe", _typeequipe, nullable=True),
        sa.Column("annee", sa.Integer(), nullable=False),
        sa.Column("mois", sa.Integer(), nullable=False),
        sa.Column("jours", sa.Float(), nullable=False, server_default="0"),
        sa.UniqueConstraint("evolution_code", "matricule", "annee", "mois", name="uq_temps_consomme"),
    )

    op.create_table(
        "snapshots_atterrissage",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evolution_code", sa.String(50), sa.ForeignKey("evolutions.code"), nullable=False),
        sa.Column("annee", sa.Integer(), nullable=False),
        sa.Column("mois", sa.Integer(), nullable=False),
        sa.Column("raf_dev", sa.Float(), nullable=True),
        sa.Column("raf_testing", sa.Float(), nullable=True),
        sa.Column("raf_total", sa.Float(), nullable=True),
        sa.Column("date_fin_estimee", sa.Date(), nullable=True),
        sa.Column("temps_dev_consomme", sa.Float(), nullable=True),
        sa.Column("temps_testing_consomme", sa.Float(), nullable=True),
        sa.Column("date_snapshot", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("evolution_code", "annee", "mois", name="uq_snapshot"),
    )

    op.create_table(
        "time_niv2_mappings",
        sa.Column("time_niv2", sa.String(150), primary_key=True),
        sa.Column("code_equipe", sa.String(20), sa.ForeignKey("equipes.code"), nullable=False),
        sa.Column("type_equipe", _typeequipe, nullable=False),
    )

    op.create_table(
        "taches_hors_evolutions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("time_niv2", sa.String(100), nullable=False),
        sa.Column("nom_tache", sa.String(500), nullable=True),
        sa.Column("matricule", sa.String(20), nullable=False, server_default=""),
        sa.Column("nom_ressource", sa.String(100), nullable=True),
        sa.Column("annee", sa.Integer(), nullable=False),
        sa.Column("mois", sa.Integer(), nullable=False),
        sa.Column("jours", sa.Float(), nullable=False, server_default="0"),
        sa.UniqueConstraint("time_niv2", "nom_tache", "matricule", "annee", "mois", name="uq_tache_hors_evol"),
    )

    op.create_table(
        "historique_imports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("type_import", sa.String(20), nullable=False),
        sa.Column("nom_fichier", sa.String(200), nullable=True),
        sa.Column("date_import", sa.DateTime(), nullable=True),
        sa.Column("nb_crees", sa.Integer(), server_default="0"),
        sa.Column("nb_mis_a_jour", sa.Integer(), server_default="0"),
        sa.Column("nb_ignores", sa.Integer(), server_default="0"),
        sa.Column("nb_erreurs", sa.Integer(), server_default="0"),
        sa.Column("detail", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("historique_imports")
    op.drop_table("taches_hors_evolutions")
    op.drop_table("time_niv2_mappings")
    op.drop_table("snapshots_atterrissage")
    op.drop_table("temps_consommes")
    op.drop_table("ressources")
    op.drop_table("historique_etapes")
    op.drop_table("etapes_cycle_vie")
    op.drop_table("evolutions")
    op.drop_table("workspace_mappings")
    op.drop_table("releases")
    op.drop_table("equipes")
    bind = op.get_bind()
    ENUM(name="numeroetape").drop(bind, checkfirst=True)
    ENUM(name="statutetape").drop(bind, checkfirst=True)
    ENUM(name="typeequipe").drop(bind, checkfirst=True)
