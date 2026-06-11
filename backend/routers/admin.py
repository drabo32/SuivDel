from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Equipe, Release, WorkspaceMapping, Ressource, TimeNiv2Mapping
from schemas import EquipeSchema, ReleaseSchema, ReleaseCreate, WorkspaceMappingSchema, RessourceSchema, RessourceCreate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/equipes", response_model=List[EquipeSchema])
def get_equipes(db: Session = Depends(get_db)):
    return db.query(Equipe).order_by(Equipe.libelle).all()


@router.get("/releases", response_model=List[ReleaseSchema])
def get_releases(db: Session = Depends(get_db)):
    return db.query(Release).order_by(Release.annee.desc(), Release.mois.desc()).all()


@router.post("/releases", response_model=ReleaseSchema)
def create_release(data: ReleaseCreate, db: Session = Depends(get_db)):
    existing = db.query(Release).filter(Release.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Release déjà existante")
    release = Release(**data.model_dump())
    db.add(release)
    db.commit()
    db.refresh(release)
    return release


@router.put("/releases/{code}")
def update_release(code: str, data: ReleaseCreate, db: Session = Depends(get_db)):
    release = db.query(Release).filter(Release.code == code).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release non trouvée")
    for field, value in data.model_dump().items():
        setattr(release, field, value)
    db.commit()
    return {"ok": True}


@router.get("/workspaces", response_model=List[WorkspaceMappingSchema])
def get_workspaces(db: Session = Depends(get_db)):
    return db.query(WorkspaceMapping).all()


@router.put("/workspaces/{workspace}")
def update_workspace(workspace: str, code_equipe: str, db: Session = Depends(get_db)):
    mapping = db.query(WorkspaceMapping).filter(WorkspaceMapping.workspace_aha == workspace).first()
    if not mapping:
        db.add(WorkspaceMapping(workspace_aha=workspace, code_equipe=code_equipe))
    else:
        mapping.code_equipe = code_equipe
    db.commit()
    return {"ok": True}


@router.get("/ressources", response_model=List[RessourceSchema])
def get_ressources(db: Session = Depends(get_db)):
    return db.query(Ressource).order_by(Ressource.nom).all()


@router.post("/ressources", response_model=RessourceSchema)
def create_ressource(data: RessourceCreate, db: Session = Depends(get_db)):
    existing = db.query(Ressource).filter(Ressource.matricule == data.matricule).first()
    if existing:
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing
    ressource = Ressource(**data.model_dump())
    db.add(ressource)
    db.commit()
    db.refresh(ressource)
    return ressource


@router.get("/time-niv2")
def get_time_niv2_mappings(db: Session = Depends(get_db)):
    return [{"time_niv2": m.time_niv2, "code_equipe": m.code_equipe, "type_equipe": m.type_equipe}
            for m in db.query(TimeNiv2Mapping).order_by(TimeNiv2Mapping.time_niv2).all()]


@router.post("/time-niv2")
def save_time_niv2_mapping(time_niv2: str, code_equipe: str, type_equipe: str, db: Session = Depends(get_db)):
    existing = db.query(TimeNiv2Mapping).filter(TimeNiv2Mapping.time_niv2 == time_niv2).first()
    if existing:
        existing.code_equipe = code_equipe
        existing.type_equipe = type_equipe
    else:
        db.add(TimeNiv2Mapping(time_niv2=time_niv2, code_equipe=code_equipe, type_equipe=type_equipe))
    db.commit()
    return {"ok": True}


@router.delete("/time-niv2/{time_niv2}")
def delete_time_niv2_mapping(time_niv2: str, db: Session = Depends(get_db)):
    m = db.query(TimeNiv2Mapping).filter(TimeNiv2Mapping.time_niv2 == time_niv2).first()
    if m:
        db.delete(m)
        db.commit()
    return {"ok": True}


@router.delete("/ressources/{matricule}")
def delete_ressource(matricule: str, db: Session = Depends(get_db)):
    ressource = db.query(Ressource).filter(Ressource.matricule == matricule).first()
    if not ressource:
        raise HTTPException(status_code=404, detail="Ressource non trouvée")
    db.delete(ressource)
    db.commit()
    return {"ok": True}
