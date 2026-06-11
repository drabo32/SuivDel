# Suivi Évolutions — Guide de reconstruction complète

Ce document permet de recréer l'application **Suivi Évolutions ACTIV'Infinite** de zéro, avec tout le code source, la configuration et les décisions d'architecture.

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Stack technique](#2-stack-technique)
3. [Structure des fichiers](#3-structure-des-fichiers)
4. [Infrastructure Docker](#4-infrastructure-docker)
5. [Base de données — modèles et schéma](#5-base-de-données--modèles-et-schéma)
6. [Backend FastAPI](#6-backend-fastapi)
7. [Frontend React](#7-frontend-react)
8. [Imports de données](#8-imports-de-données)
9. [Règles métier importantes](#9-règles-métier-importantes)
10. [Procédure de déploiement](#10-procédure-de-déploiement)
11. [Pièges connus et solutions](#11-pièges-connus-et-solutions)

---

## 1. Vue d'ensemble

Application web de suivi du développement des évolutions logicielles pour le produit ACTIV'Infinite.

**Fonctionnalités principales :**
- Suivi des évolutions par équipe, par release, par statut
- Cycle de vie en 5 étapes : Analyse PO → Développement → Recette interne → Livraison intégration → Recette Pôle Testing
- Import des évolutions depuis Aha! (CSV)
- Import des temps consommés depuis ChangePoint (CSV)
- Import d'initialisation depuis un fichier SuiviDelivery (CSV) — RAF, chiffrages, dates
- Dashboard global, par équipe, par release, testing, atterrissage
- Suivi des temps « hors évolutions » (03-Edition) avec RAF saisissable par tâche
- Snapshots mensuels d'atterrissage (RAFs + dates fin estimées)
- Verrouillage optimiste sur les évolutions et les étapes (`version_verrou`)

---

## 2. Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| BDD | PostgreSQL | 16-alpine |
| Backend | FastAPI + SQLAlchemy | FastAPI 0.111, SA 2.0.30 |
| Migrations | Alembic | 1.13.1 |
| Validation | Pydantic | 2.7.1 |
| Serveur ASGI | Uvicorn | 0.30.1 |
| Frontend | React + Vite | React 18.3, Vite 5.2 |
| UI | Ant Design | 5.17.4 |
| Graphiques | Recharts | 2.12.7 |
| Routeur | react-router-dom | 6.23 |
| Infra | Docker + Docker Compose | — |
| Reverse proxy | Nginx (alpine) | — |

---

## 3. Structure des fichiers

```
suivi-evolutions/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 0001_initial_schema.py
│   │       ├── 0002_raf_hors_evolutions.py
│   │       ├── 0003_historique_diff_release.py
│   │       ├── 0004_budget_initial.py
│   │       ├── 0005_drop_budget_initial.py
│   │       ├── 0006_etapes_analyse_pm_ppo.py
│   │       ├── 0007_conso_2025.py
│   │       └── 0008_statut_auto_sans_bloque.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── evolutions.py
│   │   ├── etapes.py
│   │   ├── snapshots.py
│   │   ├── imports.py
│   │   ├── dashboards.py
│   │   └── admin.py
│   └── services/
│       ├── __init__.py
│       ├── import_aha.py
│       ├── import_changepoint.py
│       └── import_init.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js  (généré par npm create vite)
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/
        │   └── client.js
        └── pages/
            ├── Evolutions.jsx
            ├── EvolutionDetail.jsx
            ├── Import.jsx
            ├── Admin.jsx
            ├── DashboardGlobal.jsx
            ├── DashboardEquipe.jsx
            ├── DashboardTesting.jsx
            ├── DashboardAtterrissage.jsx
            ├── DashboardRelease.jsx
            ├── HistoriqueRelease.jsx
            └── HorsEvolutions.jsx
```

---

## 4. Infrastructure Docker

### `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16-alpine
    pull_policy: if_not_present
    environment:
      POSTGRES_DB: suivi_evolutions
      POSTGRES_USER: suivi
      POSTGRES_PASSWORD: suivi2026
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U suivi -d suivi_evolutions"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://suivi:suivi2026@db:5432/suivi_evolutions
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### `backend/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.7.1
python-multipart==0.0.9
```

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### `frontend/nginx.conf`

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    client_max_body_size 100M;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

> **Important :** `client_max_body_size 100M` est indispensable pour l'upload des fichiers CSV volumineux (ChangePoint notamment).

---

## 5. Base de données — modèles et schéma

### `backend/database.py`

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://suivi:suivi2026@localhost:5432/suivi_evolutions")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `backend/models.py`

```python
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
    # "Bloqué" supprimé — statut entièrement dérivé du pourcentage ou de la date réelle


class NumeroEtape(str, enum.Enum):
    ANALYSE_PM = "Analyse PM"           # nouveau
    ANALYSE_PO = "Analyse PO"
    ANALYSE_PPO = "Analyse PPO"         # nouveau
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
    budget = Column(Float, nullable=True)       # "Master feature initial estimate" Aha (priorité) ou "Macro chiffrage"
    conso_2025 = Column(Float, nullable=True)   # Consommé 2025 depuis SuiviDelivery
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
    type_equipe = Column(Enum(TypeEquipe), nullable=True)

    equipe_obj = relationship("Equipe", back_populates="ressources")


class TempsConsomme(Base):
    __tablename__ = "temps_consommes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    evolution_code = Column(String(50), ForeignKey("evolutions.code"), nullable=False)
    matricule = Column(String(20), nullable=False)
    nom_ressource = Column(String(100), nullable=True)
    code_equipe = Column(String(20), nullable=True)
    type_equipe = Column(Enum(TypeEquipe), nullable=True)
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
    date_fin_estimee = Column(Date, nullable=True)
    temps_dev_consomme = Column(Float, nullable=True)
    temps_testing_consomme = Column(Float, nullable=True)
    date_snapshot = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("evolution_code", "annee", "mois"),)

    evolution = relationship("Evolution", back_populates="snapshots")


class TimeNiv2Mapping(Base):
    __tablename__ = "time_niv2_mappings"
    time_niv2 = Column(String(150), primary_key=True)
    code_equipe = Column(String(20), ForeignKey("equipes.code"), nullable=False)
    type_equipe = Column(Enum(TypeEquipe), nullable=False)


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
```

### Schéma des tables (résumé)

| Table | Clé primaire | Description |
|-------|-------------|-------------|
| `equipes` | `code` | Équipes DEV et TESTING |
| `releases` | `code` | Releases avec version, mois, année |
| `workspace_mappings` | `workspace_aha` | Workspace Aha! → équipe |
| `evolutions` | `code` | Évolutions (master features Aha!) |
| `etapes_cycle_vie` | `id` | 7 étapes par évolution, UniqueConstraint(code, etape) |
| `historique_etapes` | `id` | Audit des modifications d'étapes |
| `ressources` | `matricule` | Collaborateurs |
| `temps_consommes` | `id` | Temps par (évolution, matricule, année, mois) |
| `snapshots_atterrissage` | `id` | Snapshot mensuel RAF + date fin |
| `time_niv2_mappings` | `time_niv2` | Time_Niv2 ChangePoint → équipe |
| `taches_hors_evolutions` | `id` | Temps hors-évolutions par (time_niv2, tache, matricule, année, mois) |
| `rafs_hors_evolutions` | `id` | RAF manuel par tâche hors-évolution |
| `historique_imports` | `id` | Log des imports |
| `historique_diff_release` | `id` | Diffs import Aha par release (AJOUT/SUPPRESSION/CHANGEMENT_STATUT) |

---

## 6. Backend FastAPI

### `backend/alembic.ini`

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s
truncate_slug_length = 40

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### `backend/alembic/env.py`

```python
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://suivi:suivi2026@localhost:5432/suivi_evolutions",
)


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### `backend/alembic/versions/0001_initial_schema.py`

```python
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

_typeequipe   = ENUM("DEV", "TESTING", name="typeequipe",   create_type=False)
_statutetape  = ENUM("À faire", "En cours", "Terminé", "Bloqué", name="statutetape", create_type=False)
_numeroetape  = ENUM(
    "Analyse PO", "Développement", "Recette interne",
    "Livraison intégration", "Recette Pôle Testing",
    name="numeroetape", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
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
```

### `backend/alembic/versions/0002_raf_hors_evolutions.py`

```python
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
```

### `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models  # noqa: F401
from routers import evolutions, etapes, imports, snapshots, dashboards, admin


def run_migrations():
    import os
    from alembic.config import Config
    from alembic import command
    cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    command.upgrade(cfg, "head")


run_migrations()

app = FastAPI(title="Suivi Évolutions", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evolutions.router)
app.include_router(etapes.router)
app.include_router(imports.router)
app.include_router(snapshots.router)
app.include_router(dashboards.router)
app.include_router(admin.router)


@app.on_event("startup")
def seed_donnees_initiales():
    from database import SessionLocal
    from models import Equipe, TypeEquipe, WorkspaceMapping
    db = SessionLocal()
    try:
        equipes = [
            ("PREV", "Prévoyance", TypeEquipe.DEV),
            ("BI", "Business Intelligence", TypeEquipe.DEV),
            ("EASY", "EasyColl-DSN", TypeEquipe.DEV),
            ("CONT", "Contrat", TypeEquipe.DEV),
            ("SANTE", "Santé", TypeEquipe.DEV),
            ("AIB", "AI-Beyond", TypeEquipe.DEV),
            ("PRDG", "PRDG", TypeEquipe.DEV),
            ("ARCHI", "Archi", TypeEquipe.DEV),
            ("RSB", "RSB", TypeEquipe.DEV),
            ("TESTING", "Pôle Testing", TypeEquipe.TESTING),
        ]
        for code, libelle, type_eq in equipes:
            if not db.query(Equipe).filter(Equipe.code == code).first():
                db.add(Equipe(code=code, libelle=libelle, type_equipe=type_eq))

        workspaces = [
            ("Prestations Prévoyance", "PREV"),
            ("Business Intelligence", "BI"),
            ("Easy Collectif", "EASY"),
            ("WebDSN", "EASY"),
            ("Activ'Infinite Socle de base", "CONT"),
            ("Cotisations/Encaissement", "CONT"),
            ("Vie Entière", "CONT"),
            ("Prestations Santé", "SANTE"),
            ("AI-Beyond", "AIB"),
            ("PRDG", "PRDG"),
            ("Socle technique", "ARCHI"),
            ("BI BEYOND", "RSB"),
        ]
        for workspace, equipe in workspaces:
            if not db.query(WorkspaceMapping).filter(WorkspaceMapping.workspace_aha == workspace).first():
                db.add(WorkspaceMapping(workspace_aha=workspace, code_equipe=equipe))

        time_niv2_mappings = [
            ("0343-AI Contrat/Cotisations",              "CONT",    TypeEquipe.DEV),
            ("0342-Easy Collectif",                      "EASY",    TypeEquipe.DEV),
            ("0346-AI Prévoyance",                       "PREV",    TypeEquipe.DEV),
            ("0345-AI Prestations Santé",                "SANTE",   TypeEquipe.DEV),
            ("0361-Convergence Recette Activ Infinite",  "TESTING", TypeEquipe.TESTING),
            ("0362-Convergence TNR Activ Infinite",      "TESTING", TypeEquipe.TESTING),
            ("0347-AI  BI-PRDG",                         "PRDG",    TypeEquipe.DEV),
            ("0348-AI Architecture Technique & Dots",    "ARCHI",   TypeEquipe.DEV),
            ("0349-AI  Wébisation",                      "AIB",     TypeEquipe.DEV),
        ]
        for time_niv2, code_equipe, type_equipe in time_niv2_mappings:
            if not db.query(TimeNiv2Mapping).filter(TimeNiv2Mapping.time_niv2 == time_niv2).first():
                db.add(TimeNiv2Mapping(time_niv2=time_niv2, code_equipe=code_equipe, type_equipe=type_equipe))

        releases = [
            ("R1", "Novembre 2025", "R1", 11, 2025),
            ("R2", "Mai 2025",      "R2",  5, 2025),
            ("R3", "Novembre 2026", "R3", 11, 2026),
            ("R4", "Mai 2026",      "R4",  5, 2026),
        ]
        for code, libelle, version, mois, annee in releases:
            existing = db.query(Release).filter(Release.code == code).first()
            if existing:
                existing.libelle = libelle
                existing.version = version
                existing.mois = mois
                existing.annee = annee
            else:
                db.add(Release(code=code, libelle=libelle, version=version, mois=mois, annee=annee))

        db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
```

### `backend/schemas.py`

Voir le fichier source — il contient les Pydantic schemas pour : `EquipeSchema`, `ReleaseSchema`, `ReleaseCreate`, `WorkspaceMappingSchema`, `EtapeSchema`, `EtapeUpdate`, `EvolutionSchema`, `EvolutionUpdate`, `EvolutionListItem`, `TempsConsommeSchema`, `SnapshotSchema`, `RessourceSchema`, `RessourceCreate`, `TacheHorsEvolutionSchema`, `HistoriqueImportSchema`, `HistoriqueEtapeSchema`.

### Routers — points clés

**`routers/evolutions.py`**
- `GET /evolutions` — filtres : equipe, release, type_evolution, statut_aha, active_only
- `GET /evolutions/{code}` — détail + étapes triées dans l'ordre `ORDRE_ETAPES`
- `PUT /evolutions/{code}` — mise à jour avec contrôle `version_verrou` (409 si conflit)
- `GET /evolutions/{code}/temps` — détail des temps consommés

**`routers/etapes.py`**
- `PUT /etapes/{id}` — mise à jour avec `version_verrou` + historique automatique
- `GET /etapes/historique/{evolution_code}` — audit

**`routers/snapshots.py`**
- `POST /snapshots/{code}` — crée ou écrase le snapshot du mois courant
- `GET /snapshots/{code}` — liste des snapshots

**`routers/admin.py`**
- CRUD releases, équipes (lecture seule), workspaces, ressources, time_niv2_mappings

**`routers/imports.py`**
- `POST /imports/aha` — import CSV Aha!
- `POST /imports/changepoint` — import CSV ChangePoint
- `POST /imports/init` — import CSV SuiviDelivery
- `GET /imports/historique` — derniers 50 imports

**`routers/dashboards.py`**
- `GET /dashboards/global` — synthèse globale (filtres release, equipe)
- `GET /dashboards/equipe/{code}` — tableau évolutions + hors-évolutions + RAF total
- `GET /dashboards/testing` — évolutions en attente de recette testing
- `GET /dashboards/atterrissage` — glissement RAF mois courant vs précédent
- `GET /dashboards/release/{code}` — avancement par release
- `GET /dashboards/hors-evolutions` — tableau pivot tâches hors-évolutions (filtres année, mois, équipe)
- `PUT /dashboards/hors-evolutions-raf` — sauvegarde du RAF d'une tâche
- `GET /dashboards/controle-aha` — liste les évolutions `statut_aha = "Non importé Aha"` (squelettes ChangePoint)

---

## 7. Frontend React

### `frontend/package.json`

```json
{
  "name": "suivi-evolutions",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "antd": "^5.17.4",
    "@ant-design/icons": "^5.3.7",
    "recharts": "^2.12.7",
    "dayjs": "^1.11.11"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.2.11"
  }
}
```

### `frontend/src/api/client.js`

```javascript
const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (res.status === 409) throw new Error('Conflit de concurrence — rechargez les données')
  if (!res.ok) throw new Error(`Erreur ${res.status}`)
  return res.json()
}

export const api = {
  // Evolutions
  getEvolutions: (params = {}) => request('/evolutions?' + new URLSearchParams(params)),
  getEvolution: (code) => request(`/evolutions/${code}`),
  updateEvolution: (code, data) => request(`/evolutions/${code}`, { method: 'PUT', body: JSON.stringify(data) }),
  getTempsEvolution: (code) => request(`/evolutions/${code}/temps`),

  // Etapes
  updateEtape: (id, data) => request(`/etapes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getHistoriqueEtapes: (code) => request(`/etapes/historique/${code}`),

  // Snapshots
  creerSnapshot: (code) => request(`/snapshots/${code}`, { method: 'POST' }),
  getSnapshots: (code) => request(`/snapshots/${code}`),

  // Imports
  importAha: (file) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/imports/aha`, { method: 'POST', body: form })
      .then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json() })
  },
  importChangepoint: (file) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/imports/changepoint`, { method: 'POST', body: form })
      .then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json() })
  },
  importInit: (file) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/imports/init`, { method: 'POST', body: form })
      .then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json() })
  },
  getHistoriqueImports: () => request('/imports/historique'),

  // Dashboards
  getDashboardGlobal: (params = {}) => request('/dashboards/global?' + new URLSearchParams(params)),
  getDashboardEquipe: (code, params = {}) => request(`/dashboards/equipe/${code}?` + new URLSearchParams(params)),
  getDashboardTesting: (params = {}) => request('/dashboards/testing?' + new URLSearchParams(params)),
  getDashboardAtterrissage: (params = {}) => request('/dashboards/atterrissage?' + new URLSearchParams(params)),
  getDashboardRelease: (code) => request(`/dashboards/release/${code}`),
  getHorsEvolutions: (params = {}) => request('/dashboards/hors-evolutions?' + new URLSearchParams(params)),
  updateRafHorsEvolution: (time_niv2, nom_tache, raf) =>
    request(`/dashboards/hors-evolutions-raf?time_niv2=${encodeURIComponent(time_niv2)}&nom_tache=${encodeURIComponent(nom_tache)}&raf=${raf}`, { method: 'PUT' }),

  // Admin
  getEquipes: () => request('/admin/equipes'),
  getReleases: () => request('/admin/releases'),
  createRelease: (data) => request('/admin/releases', { method: 'POST', body: JSON.stringify(data) }),
  updateRelease: (code, data) => request(`/admin/releases/${code}`, { method: 'PUT', body: JSON.stringify(data) }),
  getWorkspaces: () => request('/admin/workspaces'),
  updateWorkspace: (workspace, code_equipe) =>
    request(`/admin/workspaces/${encodeURIComponent(workspace)}?code_equipe=${code_equipe}`, { method: 'PUT' }),
  getRessources: () => request('/admin/ressources'),
  saveRessource: (data) => request('/admin/ressources', { method: 'POST', body: JSON.stringify(data) }),
  deleteRessource: (matricule) => request(`/admin/ressources/${matricule}`, { method: 'DELETE' }),
  getTimeNiv2Mappings: () => request('/admin/time-niv2'),
  saveTimeNiv2Mapping: (time_niv2, code_equipe, type_equipe) =>
    request(`/admin/time-niv2?time_niv2=${encodeURIComponent(time_niv2)}&code_equipe=${code_equipe}&type_equipe=${type_equipe}`, { method: 'POST' }),
  deleteTimeNiv2Mapping: (time_niv2) => request(`/admin/time-niv2/${encodeURIComponent(time_niv2)}`, { method: 'DELETE' }),
}
```

### Pages frontend — résumé

| Page | Route | Description |
|------|-------|-------------|
| `DashboardGlobal` | `/` | Statuts Aha, temps DEV/macro par équipe, avancement étapes |
| `Evolutions` | `/evolutions` | Liste filtrée + colonnes avancement |
| `EvolutionDetail` | `/evolutions/:code` | Détail : chiffrage, RAF, étapes éditables, temps, snapshots |
| `DashboardEquipe` | `/dashboard/equipe` | 6 stats, graphiques, tableau évolutions + hors-évolutions avec RAF éditables |
| `DashboardTesting` | `/dashboard/testing` | Évolutions en attente de recette testing |
| `DashboardAtterrissage` | `/dashboard/atterrissage` | Glissement mensuel RAF + date fin |
| `DashboardRelease` | `/dashboard/release` | Avancement par release |
| `HistoriqueRelease` | `/historique-release` | Historique des diffs de contenu par release (ajouts/suppressions/changements) |
| `HorsEvolutions` | `/hors-evolutions` | Tableau pivot tâches (temps + RAF éditables) + détail collaborateurs |
| `ControleAha` | `/controle-aha` | Évolutions créées par ChangePoint sans import Aha (squelettes à compléter) |
| `Import` | `/import` | Upload AHA / ChangePoint / Init + historique |
| `Admin` | `/admin` | Releases, workspaces, ressources, mappings Time_Niv2 |

---

## 8. Imports de données

### Import Aha! (CSV)

**Séparateur :** `;` | **Encodage :** UTF-8 BOM

**Colonnes utilisées :**
- `Master feature reference #` → `Evolution.code` (format : `XXX-E-NNNNN`)
- `Master feature name` → `Evolution.libelle`
- `Workspace name` → résolu via `WorkspaceMapping` → `code_equipe`
- `Release name` → matching par `contains` sur `Release.version` ou `Release.libelle`
- `Master feature status` → `statut_aha` (si "Abandonnée" → `active=False`)
- `Master feature initial estimate` (priorité) ou `Macro chiffrage` → `budget`
- `Type évolution` → `type_evolution`
- `To-do due date` → `date_reelle` de l'étape **Analyse PM** (si renseignée, statut → Terminé)

**Comportement :** upsert — crée les étapes initiales (7 étapes, statut "À faire") lors de la création. Génère des diffs `HistoriqueDiffRelease` (AJOUT/SUPPRESSION/CHANGEMENT_STATUT) à chaque import.

**Détection auto du séparateur :** `csv.Sniffer` détecte `;` ou `,`.

> Si une évolution Aha est déjà en base avec `statut_aha = "Non importé Aha"` (squelette ChangePoint), l'import Aha la met à jour normalement avec les vraies données.

### Import ChangePoint (CSV)

**Séparateur :** `;` | **Encodage :** auto-détecté (utf-8-sig → utf-8 → latin-1 → cp1252)

**Colonnes utilisées :**
- `ApprovalStatus` — seules les lignes `"A"` sont traitées
- `RegularDay` — jours (décimale avec virgule)
- `Time_Niv0` — si `"03-Edition"` → tâche hors-évolution
- `Time_Niv2` — identifiant de périmètre ChangePoint
- `Task` — si contient un code `XXX-E-NNNNN` → temps évolution, sinon `nom_tache`
- `Matricule`, `ressource` — collaborateur
- `Année`, `Mois` ou `TimeDate` (DD/MM/YYYY) — période

**Logique :**
- Ligne avec code AHA dans `Task` → `TempsConsomme` (upsert par évolution+matricule+année+mois)
- Ligne `Time_Niv0 = "03-Edition"` sans code AHA → `TacheHorsEvolution` (upsert par time_niv2+nom_tache+matricule+année+mois)
- `Time_Niv2` doit être mappé dans `time_niv2_mappings` pour rattacher à une équipe

### Import Init / SuiviDelivery (CSV)

**Séparateur :** `;` | **Encodage :** auto-détecté

**Particularités :**
- En-têtes multilignes (cellules avec sauts de ligne) → utiliser `csv.reader` (pas `DictReader`) + normaliser les en-têtes
- Colonnes dupliquées (même nom pour DEV et CVG) → repérer par position (`find_col()`)
- Dates au format numérique Excel (serial) → `datetime(1899, 12, 30) + timedelta(days=serial)`

**Colonnes utilisées :**

*Champs évolution :*
- `Ref. Aha Master feature` → code évolution (clé)
- `Macro Chiffrage` → `macro_chiffrage`
- `Chiffrage Edition` → `chiffrage_edition`
- `RAF DEV M` → `raf_dev`
- `RAF CVG M` → `raf_testing`
- `Conso 2025` → `conso_2025`

*Champs étapes :*
- `date prévisionnelle presentation fiche initiative (PM)` → `date_prevue` d'Analyse PM
- `date prévisionnelle fin instruction PO` → `date_prevue` d'Analyse PO
- `PO/PPO` → `responsable` d'Analyse PO
- `date prévisionnelle fin instruction PPO` → `date_prevue` d'Analyse PPO
- `% R7 Intégra.tion` → `pourcentage_avancement` de Recette interne (valeur décimale × 100)
- `date previsionnelle mise à dispo CVG` → `date_prevue` de Livraison intégration
- `date réelle mise à dispo V8` → `date_reelle` de Livraison intégration
- `% Recette CVG V8` → `pourcentage_avancement` de Recette Pôle Testing (valeur décimale × 100)
- `Testeur CVG` → `responsable` de Recette Pôle Testing
- `Charge estimée (S, M, L, XL)` → `commentaire` de Recette Pôle Testing

**Comportement :** mise à jour uniquement des évolutions déjà en base (pas de création). Statut des étapes recalculé automatiquement après chaque mise à jour (règles métier).

**Important :** `_normalize()` collapse les espaces multiples (`" ".join(s.split())`) pour matcher les en-têtes avec double espace dans le fichier source.

---

## 9. Règles métier importantes

### Ordre des étapes
Les 7 étapes sont toujours affichées et triées dans cet ordre immuable :
1. Analyse PM
2. Analyse PO
3. Analyse PPO
4. Développement
5. Recette interne
6. Livraison intégration
7. Recette Pôle Testing

Le backend trie explicitement avec `ORDRE_ETAPES.index()` dans `get_evolution()`.

### Règles de calcul automatique du statut d'étape

Le statut n'est **jamais saisi manuellement** — il est toujours recalculé à chaque sauvegarde et à chaque import Init.

| Étape | Règle |
|-------|-------|
| **Livraison intégration** | `date_reelle` renseignée → **Terminé** / absente → **À faire** (pas de pourcentage pour cette étape) |
| Toutes les autres | 0 % → **À faire** / 1–99 % → **En cours** / 100 % → **Terminé** |

Le select "Statut" est absent du formulaire d'édition des étapes dans l'UI. Le champ "%" est absent pour "Livraison intégration".

### Verrouillage optimiste
Évolutions et étapes ont un champ `version_verrou` (entier). À chaque PUT, le client envoie la version qu'il a lue. Si elle diffère de celle en base → HTTP 409. Le frontend affiche un message "rechargez les données".

### Matching release lors de l'import Aha
La colonne `Release name` du CSV Aha ne contient pas toujours exactement le libellé ou la version stockée. Le matching se fait par **contient insensible à la casse** (dans les deux sens) :
```python
release_libelle_low = release_libelle.lower()
if (r.version.lower() in release_libelle_low
        or r.libelle.lower() in release_libelle_low
        or release_libelle_low in r.libelle.lower()):
```

### Temps hors-évolutions
- Seules les lignes ChangePoint où `Time_Niv0 = "03-Edition"` et sans code AHA dans `Task` sont des tâches hors-évolutions.
- Le RAF des tâches hors-évolutions est saisi manuellement dans l'UI (table `rafs_hors_evolutions`).
- Le dashboard équipe calcule : `raf_global = raf_évolutions + raf_hors_évolutions`.

### Snapshot atterrissage
Déclenché manuellement depuis la page détail d'une évolution. Enregistre le RAF du moment + la date fin estimée + les temps consommés. Permet de voir le glissement d'un mois sur l'autre dans le dashboard atterrissage.

---

## 10. Procédure de déploiement

### Premier déploiement (base vide)

```bash
# Depuis le dossier suivi-evolutions/
docker compose up --build -d
```

Les migrations Alembic sont jouées automatiquement au démarrage du backend (`run_migrations()` dans `main.py`). Les équipes et workspaces initiaux sont semés par `seed_donnees_initiales()`.

**Ordre de démarrage :** la base de données doit être `healthy` avant que le backend démarre (`depends_on: condition: service_healthy`).

### Reconstruction complète (reset total)

```bash
docker compose down -v          # supprime les volumes (données perdues !)
docker compose up --build -d
```

### Mise à jour de l'application

```bash
docker compose up --build -d    # rebuild les images, applique les nouvelles migrations
```

### Ajout d'une migration Alembic

1. Créer le fichier `backend/alembic/versions/000N_description.py` en incrémentant le numéro de révision
2. Renseigner `revision`, `down_revision` (= révision précédente)
3. Implémenter `upgrade()` et `downgrade()`
4. La migration sera jouée automatiquement au prochain démarrage du backend

> **Attention ENUM PostgreSQL :** pour créer un type ENUM, utiliser `ENUM(...).create(bind, checkfirst=True)` **avant** le `op.create_table`. Dans les colonnes du `create_table`, utiliser `ENUM(..., create_type=False)` pour éviter la double création.

### Accès

| Service | URL |
|---------|-----|
| Application | http://localhost:3000 |
| API FastAPI | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (user: suivi, password: suivi2026, db: suivi_evolutions) |

---

## 11. Pièges connus et solutions

### 502 Bad Gateway au démarrage
Le backend ne démarre pas si la BDD n'est pas prête. Solution : `depends_on: condition: service_healthy` dans `docker-compose.yml`. Si ça persiste après un arrêt/relance : `docker compose up -d` puis attendre, ne pas relancer tout de suite.

### Erreur 413 (Request Entity Too Large) sur l'upload
Ajouter `client_max_body_size 100M` dans `nginx.conf`. Déjà présent dans la config actuelle.

### "Unexpected token '<'" en réponse JSON
Nginx renvoie la page 404 HTML au lieu du JSON. Cause : `location /api/` ne trouve pas la route. Vérifier le `proxy_pass` et que le backend tourne.

### ENUM PostgreSQL en double lors des migrations
Symptôme : `ERROR: type "typeequipe" already exists`. Solution : ne jamais laisser SQLAlchemy créer les ENUM automatiquement. Dans les migrations, utiliser `ENUM(...).create(bind, checkfirst=True)` et `create_type=False` dans les colonnes.

### `back_populates` manquant
SQLAlchemy 2.x est strict sur les `back_populates` : si un côté de la relation est déclaré sans l'autre, crash au démarrage. Ne pas ajouter de `relationship` côté `Ressource` vers `TempsConsomme` — `TempsConsomme` n'a pas de `back_populates` vers `Ressource`.

### En-têtes multilignes dans SuiviDelivery.csv
`csv.DictReader` ne gère pas les cellules contenant des sauts de ligne (entre guillemets). Utiliser `csv.reader` et traiter l'en-tête manuellement avec `_normalize(h)` (remplace `\n` par espace + strip).

### Colonnes dupliquées dans SuiviDelivery.csv
Le fichier peut avoir deux colonnes avec le même nom (ex : même intitulé pour DEV et CVG). `DictReader` ne garde que la dernière. Solution : `csv.reader` + `_find_col()` par position.

### Ordre des étapes non garanti par SQLAlchemy
Les `relationship` ne garantissent pas l'ordre. Trier explicitement côté backend (`e.etapes.sort(...)`) et côté frontend (`ETAPES.indexOf()`).
