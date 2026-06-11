from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import SnapshotAtterrissage, Evolution
from schemas import SnapshotSchema

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/{code}", response_model=List[SnapshotSchema])
def get_snapshots(code: str, db: Session = Depends(get_db)):
    return (
        db.query(SnapshotAtterrissage)
        .filter(SnapshotAtterrissage.evolution_code == code)
        .order_by(SnapshotAtterrissage.date_snapshot.desc())
        .all()
    )


@router.delete("/{snapshot_id}")
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snap = db.query(SnapshotAtterrissage).filter(SnapshotAtterrissage.id == snapshot_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot non trouvé")
    db.delete(snap)
    db.commit()
    return {"ok": True}
