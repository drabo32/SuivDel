from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import EtapeCycleVie, HistoriqueEtape
from schemas import EtapeSchema, EtapeUpdate, HistoriqueEtapeSchema

router = APIRouter(prefix="/etapes", tags=["etapes"])


@router.put("/{etape_id}")
def update_etape(etape_id: int, data: EtapeUpdate, db: Session = Depends(get_db)):
    etape = db.query(EtapeCycleVie).filter(EtapeCycleVie.id == etape_id).first()
    if not etape:
        raise HTTPException(status_code=404, detail="Étape non trouvée")
    if etape.version_verrou != data.version_verrou:
        raise HTTPException(status_code=409, detail="Conflit de concurrence — rechargez les données")

    champs = data.model_dump(exclude={"version_verrou"})
    for champ, nouvelle_valeur in champs.items():
        if nouvelle_valeur is not None:
            ancienne_valeur = getattr(etape, champ)
            if str(ancienne_valeur) != str(nouvelle_valeur):
                db.add(HistoriqueEtape(
                    evolution_code=etape.evolution_code,
                    etape=etape.etape.value,
                    champ_modifie=champ,
                    ancienne_valeur=str(ancienne_valeur) if ancienne_valeur is not None else None,
                    nouvelle_valeur=str(nouvelle_valeur),
                    modifie_par=data.modifie_par,
                ))
            setattr(etape, champ, nouvelle_valeur)

    # Règle statut selon le type d'étape
    if etape.etape.value == "Livraison intégration":
        # Déterminé par la présence d'une date réelle
        etape.statut = "Terminé" if etape.date_reelle else "À faire"
    else:
        # Dérivé du pourcentage d'avancement
        pct = etape.pourcentage_avancement or 0
        if pct == 0:
            etape.statut = "À faire"
        elif pct == 100:
            etape.statut = "Terminé"
        else:
            etape.statut = "En cours"

    etape.version_verrou += 1
    db.commit()
    return {"ok": True, "version_verrou": etape.version_verrou}


@router.get("/historique/{evolution_code}", response_model=List[HistoriqueEtapeSchema])
def get_historique_etapes(evolution_code: str, db: Session = Depends(get_db)):
    return (
        db.query(HistoriqueEtape)
        .filter(HistoriqueEtape.evolution_code == evolution_code)
        .order_by(HistoriqueEtape.date_modification.desc())
        .all()
    )
