import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import HistoriqueImport, HistoriqueDiffRelease
from schemas import HistoriqueImportSchema
from services.import_aha import import_aha
from services.import_changepoint import import_changepoint
from services.import_init import import_init
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/aha")
async def import_fichier_aha(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        result = import_aha(db, content, file.filename)

        # Extraire les diffs avant de passer result à HistoriqueImport
        diffs = result.pop("diffs", [])

        historique = HistoriqueImport(
            type_import="AHA",
            nom_fichier=file.filename,
            **result,
        )
        db.add(historique)
        db.flush()  # Nécessaire pour obtenir historique.id avant le commit

        # Persister les diffs avec l'id de l'import
        date_import = datetime.utcnow()
        for d in diffs:
            db.add(HistoriqueDiffRelease(
                id_import=historique.id,
                date_import=date_import,
                **d,
            ))

        db.commit()
        return result
    except Exception as e:
        logger.exception("Erreur import Aha: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'import.")


@router.post("/changepoint")
async def import_fichier_changepoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        result = import_changepoint(db, content, file.filename)
        historique = HistoriqueImport(
            type_import="CHANGEPOINT",
            nom_fichier=file.filename,
            **result,
        )
        db.add(historique)
        db.commit()
        return result
    except Exception as e:
        logger.exception("Erreur import ChangePoint: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'import.")


@router.post("/init")
async def import_fichier_init(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        result = import_init(db, content, file.filename)
        historique = HistoriqueImport(
            type_import="INIT",
            nom_fichier=file.filename,
            **result,
        )
        db.add(historique)
        db.commit()
        return result
    except Exception as e:
        logger.exception("Erreur import Init: %s", e)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur import Init : {e}")


@router.get("/historique", response_model=List[HistoriqueImportSchema])
def get_historique(db: Session = Depends(get_db)):
    return db.query(HistoriqueImport).order_by(HistoriqueImport.date_import.desc()).limit(50).all()
