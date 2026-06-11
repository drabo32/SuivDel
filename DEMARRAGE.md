# Suivi Évolutions — Guide de démarrage

## Prérequis

- Docker Desktop installé et démarré
- Ports 3000, 8000, 5432 disponibles

## Lancement

```bash
cd C:\Users\sbernigaud\Documents\suivi-evolutions
docker compose up --build
```

L'application est disponible sur : **http://localhost:3000**

L'API (Swagger) est disponible sur : **http://localhost:8000/docs**

## Premier démarrage

1. Aller dans **Administration > Releases** et créer les releases (ex: code `AI-MAI-2025`, libellé `AI Mai 2025`, version `8.21`, mois `5`, année `2025`)
2. Aller dans **Administration > Ressources** et rattacher les matricules ChangePoint aux équipes
3. Aller dans **Import** et importer le fichier Aha CSV
4. Importer le fichier ChangePoint CSV

## Structure du projet

```
suivi-evolutions/
├── docker-compose.yml          # Orchestration des services
├── backend/                    # API Python FastAPI
│   ├── main.py                 # Point d'entrée + seed données initiales
│   ├── models.py               # Modèle de données SQLAlchemy
│   ├── schemas.py              # Schémas Pydantic
│   ├── database.py             # Connexion PostgreSQL
│   ├── routers/                # Endpoints API
│   │   ├── evolutions.py
│   │   ├── etapes.py
│   │   ├── imports.py
│   │   ├── snapshots.py
│   │   ├── dashboards.py
│   │   └── admin.py
│   └── services/               # Logique d'import CSV
│       ├── import_aha.py
│       └── import_changepoint.py
└── frontend/                   # Application React
    └── src/pages/
        ├── Evolutions.jsx          # Liste des évolutions
        ├── EvolutionDetail.jsx     # Détail + chiffrages + atterrissage
        ├── DashboardGlobal.jsx     # Vue globale
        ├── DashboardEquipe.jsx     # Par équipe DEV
        ├── DashboardTesting.jsx    # Pôle Testing
        ├── DashboardAtterrissage.jsx  # Dérive atterrissage
        ├── DashboardRelease.jsx    # Par release
        ├── HorsEvolutions.jsx      # Activité 03-Edition
        ├── Import.jsx              # Import CSV
        └── Admin.jsx               # Administration
```

## Arrêt

```bash
docker compose down
```

Pour supprimer aussi les données (base PostgreSQL) :

```bash
docker compose down -v
```
