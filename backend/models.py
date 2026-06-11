from datetime import date, datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, DateTime,
    ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum
from database import Base


class TypeEquipe(str, enum.Enum):
    DEV = "DEV"
    TESTING = "TESTING"


class TypeEvolution(str, enum.Enum):
    REGLEMENTAIRE = "Réglementaire"
    ROADMAP = "Roadmap"
    DEDIE = "Dédié"


class StatutEtape(str, enum.Enum):
    A_FAIRE = "À faire"
    EN_COURS = "En cours"
    TERMINE = "Terminé"


class NumeroEtape(str, enum.Enum):
    ANALYSE_PM = "Analyse PM"
    ANALYSE_PO = "Analyse PO"
    ANALYSE_PPO = "Analyse PPO"
    DEVELOPPEMENT = "Développement"
    RECETTE_INTERNE = "Recette interne"
    LIVRAISON_INTEGRATION = "Livraison intégration"
    RECETTE_POLE_TESTING = "Recette Pôle Testing"


class Equipe(Base):
    __tablename__ = "equipes"
    code = Column(String(20), primary_key=True)
    libelle = Column(String(100), nullable=False)
    type_equipe = Column(Enum(TypeEquipe, values_callable=lambda obj: [e.value for e in obj]), nullable=False)

    evolutions = relationship("Evolution", back_populates="equipe_obj")
    ressources = relationship("Ressource", back_populates="equipe_obj")


class Release(Base):
    __tablename__ = "releases"
    code = Column(String(50), primary_key=True)
    libelle = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    mois = Column(Integer, nullable=False)
    annee = Column(Integer, nullable=False)

    evolutions = relationship("Evolution", back_populates="release_obj")


class WorkspaceMapping(Base):
    __tablename__ = "workspace_mappings"
    workspace_aha = Column(String(100), primary_key=True)
    code_equipe = Column(String(20), ForeignKey("equipes.code"), nullable=False)


class Evolution(Base):
    __tablename__ = "evolutions"
    code = Column(String(50), primary_key=True)
    libelle = Column(Text, nullable=False)
    code_equipe = Column(String(20), ForeignKey("equipes.code"), nullable=False)
    code_release = Column(String(50), ForeignKey("releases.code"), nullable=True)
    type_evolution = Column(String(30), nullable=True)
    statut_aha = Column(String(50), nullable=True)
    budget = Column(Float, nullable=True)            # "Master feature initial estimate" ou "Macro chiffrage" Aha
    conso_2025 = Column(Float, nullable=True)
    macro_chiffrage = Column(Float, nullable=True)
    chiffrage_edition = Column(Float, nullable=True)
    raf_dev = Column(Float, nullable=True)
    raf_testing = Column(Float, nullable=True)
    date_fin_estimee = Column(Date, nullable=True)
    active = Column(Boolean, default=True)
    date_import = Column(Date, nullable=True)
    version_verrou = Column(Integer, default=0)

    equipe_obj = relationship("Equipe", back_populates="evolutions")
    release_obj = relationship("Release", back_populates="evolutions")
    etapes = relationship("EtapeCycleVie", back_populates="evolution", cascade="all, delete-orphan")
    temps = relationship("TempsConsomme", back_populates="evolution", cascade="all, delete-orphan")
    snapshots = relationship("SnapshotAtterrissage", back_populates="evolution", cascade="all, delete-orphan")


class EtapeCycleVie(Base):
    __tablename__ = "etapes_cycle_vie"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evolution_code = Column(String(50), ForeignKey("evolutions.code"), nullable=False)
    etape = Column(Enum(NumeroEtape, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    statut = Column(Enum(StatutEtape, values_callable=lambda obj: [e.value for e in obj]), default=StatutEtape.A_FAIRE)
    date_prevue = Column(Date, nullable=True)
    date_reelle = Column(Date, nullable=True)
    pourcentage_avancement = Column(Integer, default=0)
    responsable = Column(String(100), nullable=True)
    commentaire = Column(Text, nullable=True)
    date_modification = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modifie_par = Column(String(100), nullable=True)
    version_verrou = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("evolution_code", "etape"),)

    evolution = relationship("Evolution", back_populates="etapes")


class HistoriqueEtape(Base):
    __tablename__ = "historique_etapes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evolution_code = Column(String(50), nullable=False)
    etape = Column(String(50), nullable=False)
    champ_modifie = Column(String(50), nullable=False)
    ancienne_valeur = Column(Text, nullable=True)
    nouvelle_valeur = Column(Text, nullable=True)
    modifie_par = Column(String(100), nullable=True)
    date_modification = Column(DateTime, default=datetime.utcnow)


class Ressource(Base):
    __tablename__ = "ressources"
    matricule = Column(String(20), primary_key=True)
    nom = Column(String(100), nullable=False)
    code_equipe = Column(String(20), ForeignKey("equipes.code"), nullable=True)
    type_equipe = Column(Enum(TypeEquipe, values_callable=lambda obj: [e.value for e in obj]), nullable=True)

    equipe_obj = relationship("Equipe", back_populates="ressources")


class TempsConsomme(Base):
    __tablename__ = "temps_consommes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evolution_code = Column(String(50), ForeignKey("evolutions.code"), nullable=False)
    matricule = Column(String(20), nullable=False)
    nom_ressource = Column(String(100), nullable=True)
    code_equipe = Column(String(20), nullable=True)
    type_equipe = Column(Enum(TypeEquipe, values_callable=lambda obj: [e.value for e in obj]), nullable=True)
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    jours = Column(Float, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("evolution_code", "matricule", "annee", "mois"),)

    evolution = relationship("Evolution", back_populates="temps")


class SnapshotAtterrissage(Base):
    __tablename__ = "snapshots_atterrissage"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evolution_code = Column(String(50), ForeignKey("evolutions.code"), nullable=False)
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    raf_dev = Column(Float, nullable=True)
    raf_testing = Column(Float, nullable=True)
    raf_total = Column(Float, nullable=True)
    budget = Column(Float, nullable=True)
    macro_chiffrage = Column(Float, nullable=True)
    chiffrage_edition = Column(Float, nullable=True)
    conso_2025 = Column(Float, nullable=True)
    temps_dev_consomme = Column(Float, nullable=True)
    temps_testing_consomme = Column(Float, nullable=True)
    date_snapshot = Column(DateTime, default=datetime.utcnow)

    evolution = relationship("Evolution", back_populates="snapshots")


class TimeNiv2Mapping(Base):
    __tablename__ = "time_niv2_mappings"
    time_niv2 = Column(String(150), primary_key=True)
    code_equipe = Column(String(20), ForeignKey("equipes.code"), nullable=False)
    type_equipe = Column(Enum(TypeEquipe, values_callable=lambda obj: [e.value for e in obj]), nullable=False)


class TacheHorsEvolution(Base):
    __tablename__ = "taches_hors_evolutions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time_niv2 = Column(String(100), nullable=False)
    nom_tache = Column(String(500), nullable=True)
    matricule = Column(String(20), nullable=False, default="")
    nom_ressource = Column(String(100), nullable=True)
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    jours = Column(Float, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("time_niv2", "nom_tache", "matricule", "annee", "mois"),)


class RafHorsEvolution(Base):
    """RAF saisi manuellement pour une tâche hors évolution (1 ligne par tâche)."""
    __tablename__ = "rafs_hors_evolutions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time_niv2 = Column(String(100), nullable=False)
    nom_tache = Column(String(500), nullable=False, default="")
    raf = Column(Float, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("time_niv2", "nom_tache", name="uq_raf_hors_evol"),)


class HistoriqueDiffRelease(Base):
    """Trace les entrées/sorties/changements de statut d'évolutions dans les releases, import par import."""
    __tablename__ = "historique_diff_release"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_import = Column(Integer, ForeignKey("historique_imports.id"), nullable=True)
    date_import = Column(DateTime, nullable=False, default=datetime.utcnow)
    code_release = Column(String(50), nullable=False)
    evolution_code = Column(String(50), nullable=False)
    libelle_evolution = Column(Text, nullable=True)
    type_diff = Column(String(20), nullable=False)  # AJOUT | SUPPRESSION | CHANGEMENT_STATUT
    ancienne_valeur = Column(String(200), nullable=True)
    nouvelle_valeur = Column(String(200), nullable=True)


class HistoriqueImport(Base):
    __tablename__ = "historique_imports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_import = Column(String(20), nullable=False)
    nom_fichier = Column(String(200), nullable=True)
    date_import = Column(DateTime, default=datetime.utcnow)
    nb_crees = Column(Integer, default=0)
    nb_mis_a_jour = Column(Integer, default=0)
    nb_ignores = Column(Integer, default=0)
    nb_erreurs = Column(Integer, default=0)
    detail = Column(Text, nullable=True)
