from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from models import Evolution, TempsConsomme, EtapeCycleVie, TypeEquipe
from schemas import EvolutionSchema, EvolutionUpdate, EvolutionListItem

router = APIRouter(prefix="/evolutions", tags=["evolutions"])

ORDRE_ETAPES = ["Analyse PM", "Analyse PO", "Analyse PPO", "Développement", "Recette interne", "Livraison intégration", "Recette Pôle Testing"]


@router.get("", response_model=List[EvolutionListItem])
def list_evolutions(
    equipe: Optional[str] = None,
    release: Optional[str] = None,
    type_evolution: Optional[str] = None,
    statut_aha: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Evolution)
    if active_only:
        query = query.filter(Evolution.active == True)
    if equipe:
        query = query.filter(Evolution.code_equipe == equipe)
    if release:
        query = query.filter(Evolution.code_release == release)
    if type_evolution:
        query = query.filter(Evolution.type_evolution == type_evolution)
    if statut_aha:
        query = query.filter(Evolution.statut_aha == statut_aha)

    evolutions = query.all()
    result = []
    for e in evolutions:
        temps_dev = sum(
            t.jours for t in e.temps if t.type_equipe == TypeEquipe.DEV
        )
        temps_testing = sum(
            t.jours for t in e.temps if t.type_equipe == TypeEquipe.TESTING
        )
        avancements = [et.pourcentage_avancement for et in e.etapes]
        avancement_moyen = sum(avancements) / len(avancements) if avancements else 0

        item = EvolutionListItem.model_validate(e)
        item.temps_dev = round(temps_dev, 2)
        item.temps_testing = round(temps_testing, 2)
        item.avancement_moyen = round(avancement_moyen, 1)
        result.append(item)

    return result


@router.get("/{code}", response_model=EvolutionSchema)
def get_evolution(code: str, db: Session = Depends(get_db)):
    e = db.query(Evolution).filter(Evolution.code == code).first()
    if not e:
        raise HTTPException(status_code=404, detail="Évolution non trouvée")
    e.etapes.sort(key=lambda et: ORDRE_ETAPES.index(et.etape.value) if et.etape.value in ORDRE_ETAPES else 99)
    return e


@router.put("/{code}")
def update_evolution(code: str, data: EvolutionUpdate, db: Session = Depends(get_db)):
    e = db.query(Evolution).filter(Evolution.code == code).first()
    if not e:
        raise HTTPException(status_code=404, detail="Évolution non trouvée")
    if e.version_verrou != data.version_verrou:
        raise HTTPException(status_code=409, detail="Conflit de concurrence — rechargez les données")

    _CHAMPS_SNAPSHOT = {"macro_chiffrage", "chiffrage_edition", "raf_dev", "raf_testing"}
    payload = data.model_dump(exclude={"version_verrou"})
    declenche_snapshot = any(payload.get(f) is not None for f in _CHAMPS_SNAPSHOT)

    for field, value in payload.items():
        if value is not None:
            setattr(e, field, value)
    e.version_verrou += 1

    if declenche_snapshot:
        from services.snapshot_service import creer_snapshot_auto
        creer_snapshot_auto(db, e)

    db.commit()
    return {"ok": True, "version_verrou": e.version_verrou}


@router.get("/{code}/temps")
def get_temps_evolution(code: str, db: Session = Depends(get_db)):
    temps = db.query(TempsConsomme).filter(TempsConsomme.evolution_code == code).all()
    dev_total = sum(t.jours for t in temps if t.type_equipe == TypeEquipe.DEV)
    testing_total = sum(t.jours for t in temps if t.type_equipe == TypeEquipe.TESTING)

    par_mois_dev: dict = {}
    par_mois_testing: dict = {}
    for t in temps:
        key = f"{t.annee}-{t.mois:02d}"
        if t.type_equipe == TypeEquipe.DEV:
            par_mois_dev[key] = par_mois_dev.get(key, 0) + t.jours
        else:
            par_mois_testing[key] = par_mois_testing.get(key, 0) + t.jours

    detail = [
        {
            "matricule": t.matricule,
            "nom": t.nom_ressource,
            "equipe": t.code_equipe,
            "type": t.type_equipe,
            "annee": t.annee,
            "mois": t.mois,
            "jours": t.jours,
        }
        for t in sorted(temps, key=lambda x: (x.annee, x.mois))
    ]

    return {
        "dev_total": round(dev_total, 2),
        "testing_total": round(testing_total, 2),
        "par_mois_dev": par_mois_dev,
        "par_mois_testing": par_mois_testing,
        "detail": detail,
    }
