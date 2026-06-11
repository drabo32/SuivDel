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


app = FastAPI(title="Suivi Évolutions", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def initialiser():
    # Migrations Alembic en premier, dans l'event startup (pas au niveau module)
    run_migrations()
    _seed_donnees_initiales()


def _seed_donnees_initiales():
    from sqlalchemy.exc import IntegrityError
    from database import SessionLocal
    from models import Equipe, TypeEquipe, WorkspaceMapping, TimeNiv2Mapping, Release
    db = SessionLocal()
    try:
        equipes = [
            ("PREV", "Prévoyance", TypeEquipe.DEV),
            ("BI", "BI-PRDG-RSB", TypeEquipe.DEV),
            ("EASY", "EasyColl-DSN", TypeEquipe.DEV),
            ("CONT", "Contrat", TypeEquipe.DEV),
            ("SANTE", "Santé", TypeEquipe.DEV),
            ("AIB", "AI-Beyond", TypeEquipe.DEV),
            ("ARCHI", "Archi", TypeEquipe.DEV),
            ("TESTING", "Pôle Testing", TypeEquipe.TESTING),
        ]
        for code, libelle, type_eq in equipes:
            existing = db.query(Equipe).filter(Equipe.code == code).first()
            if existing:
                existing.libelle = libelle
            else:
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
            ("PRDG", "BI"),
            ("Socle technique", "ARCHI"),
            ("BI BEYOND", "BI"),
        ]
        for workspace, equipe in workspaces:
            existing = db.query(WorkspaceMapping).filter(WorkspaceMapping.workspace_aha == workspace).first()
            if existing:
                existing.code_equipe = equipe
            else:
                db.add(WorkspaceMapping(workspace_aha=workspace, code_equipe=equipe))

        time_niv2_mappings = [
            ("0343-AI Contrat/Cotisations",              "CONT",    TypeEquipe.DEV),
            ("0342-Easy Collectif",                      "EASY",    TypeEquipe.DEV),
            ("0346-AI Prévoyance",                       "PREV",    TypeEquipe.DEV),
            ("0345-AI Prestations Santé",                "SANTE",   TypeEquipe.DEV),
            ("0361-Convergence Recette Activ Infinite",  "TESTING", TypeEquipe.TESTING),
            ("0362-Convergence TNR Activ Infinite",      "TESTING", TypeEquipe.TESTING),
            ("0347-AI BI-PRDG",                          "BI",      TypeEquipe.DEV),
            ("0348-AI Architecture Technique & Dots",    "ARCHI",   TypeEquipe.DEV),
            ("0349-AI  Wébisation",                      "AIB",     TypeEquipe.DEV),
        ]
        for time_niv2, code_equipe, type_equipe in time_niv2_mappings:
            existing = db.query(TimeNiv2Mapping).filter(TimeNiv2Mapping.time_niv2 == time_niv2).first()
            if existing:
                existing.code_equipe = code_equipe
            else:
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

        try:
            db.commit()
        except IntegrityError:
            # Race condition entre workers : un autre worker a déjà seedé — ignorer
            db.rollback()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
