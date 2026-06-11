from datetime import datetime
from sqlalchemy.orm import Session
from models import Evolution, SnapshotAtterrissage, TempsConsomme, TypeEquipe


def creer_snapshot_auto(db: Session, evolution: Evolution) -> None:
    """Crée un snapshot automatique de l'évolution (sans commit).
    À appeler avant db.commit() dans les routes et les services d'import.
    """
    temps = db.query(TempsConsomme).filter(
        TempsConsomme.evolution_code == evolution.code
    ).all()
    temps_dev = round(sum(t.jours for t in temps if t.type_equipe == TypeEquipe.DEV), 2)
    temps_testing = round(sum(t.jours for t in temps if t.type_equipe == TypeEquipe.TESTING), 2)

    raf_dev = evolution.raf_dev or 0
    raf_testing = evolution.raf_testing or 0
    raf_total = round(raf_dev + raf_testing, 2)

    now = datetime.utcnow()
    db.add(SnapshotAtterrissage(
        evolution_code=evolution.code,
        annee=now.year,
        mois=now.month,
        raf_dev=raf_dev,
        raf_testing=raf_testing,
        raf_total=raf_total,
        budget=evolution.budget,
        macro_chiffrage=evolution.macro_chiffrage,
        chiffrage_edition=evolution.chiffrage_edition,
        conso_2025=evolution.conso_2025,
        temps_dev_consomme=temps_dev,
        temps_testing_consomme=temps_testing,
        date_snapshot=now,
    ))
