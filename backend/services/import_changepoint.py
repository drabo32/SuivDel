import csv
import io
import logging
import re
from sqlalchemy.orm import Session
from models import TempsConsomme, TacheHorsEvolution, TimeNiv2Mapping, TypeEquipe
from services.utils import decoder as _decoder

logger = logging.getLogger(__name__)

CODE_AHA_PATTERN = re.compile(r"([A-Z]+-E-\d+)")
TIME_NIV0_EDITION = "03-Edition"

# Liste complète des étapes — identique à import_aha pour cohérence
_ETAPES_VALEURS = [
    "Analyse PM",
    "Analyse PO",
    "Analyse PPO",
    "Développement",
    "Recette interne",
    "Livraison intégration",
    "Recette Pôle Testing",
]
_STATUT_A_FAIRE = "À faire"


def _extraire_annee_mois(annee_raw, mois_raw, time_date):
    try:
        if annee_raw and mois_raw:
            if "/" in mois_raw:
                return int(annee_raw), int(mois_raw.split("/")[1])
            return int(annee_raw), int(mois_raw)
        if time_date and "/" in time_date:
            parts = time_date.split("/")
            if len(parts) == 3:
                return int(parts[2]), int(parts[1])
    except Exception:
        pass
    return None, None


def import_changepoint(db: Session, content: bytes, nom_fichier: str) -> dict:
    nb_traites = nb_ignores = nb_erreurs = 0
    codes_non_reconnus = set()
    time_niv2_inconnus = set()

    niv2_map = {m.time_niv2: m for m in db.query(TimeNiv2Mapping).all()}

    texte = _decoder(content)

    # Détection automatique du séparateur (même robustesse que import_aha)
    sample = texte[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"

    reader = csv.DictReader(io.StringIO(texte), delimiter=delimiter)

    cumul_evolutions: dict = {}
    cumul_hors_evol: dict = {}

    for row in reader:
        try:
            approval = (row.get("ApprovalStatus") or "").strip()
            if approval != "A":
                nb_ignores += 1
                continue

            jours_raw = (row.get("RegularDay") or "0").strip().replace(",", ".")
            jours = float(jours_raw) if jours_raw else 0.0
            if jours == 0:
                nb_ignores += 1
                continue

            time_niv0 = (row.get("Time_Niv0") or "").strip()
            time_niv2 = (row.get("Time_Niv2") or "").strip()
            task = (row.get("Task") or "").strip()
            matricule = (row.get("Matricule") or "").strip()
            nom_ressource = (row.get("ressource") or "").strip()
            time_date = (row.get("TimeDate") or "").strip()
            annee_raw = (row.get("Année") or row.get("Ann\xe9e") or "").strip()
            mois_raw = (row.get("Mois") or "").strip()

            annee, mois = _extraire_annee_mois(annee_raw, mois_raw, time_date)
            if not annee or not mois:
                nb_ignores += 1
                continue

            match = CODE_AHA_PATTERN.search(task)
            mapping = niv2_map.get(time_niv2)

            if match:
                code_aha = match.group(1)
                code_equipe = mapping.code_equipe if mapping else None
                type_equipe = mapping.type_equipe if mapping else None

                if not mapping:
                    time_niv2_inconnus.add(time_niv2)

                key = (code_aha, matricule, annee, mois)
                if key not in cumul_evolutions:
                    cumul_evolutions[key] = {
                        "jours": 0,
                        "nom_ressource": nom_ressource,
                        "code_equipe": code_equipe,
                        "type_equipe": type_equipe,
                    }
                cumul_evolutions[key]["jours"] += jours
                nb_traites += 1

            elif time_niv0 == TIME_NIV0_EDITION:
                key = (time_niv2, task, matricule, annee, mois)
                if key not in cumul_hors_evol:
                    cumul_hors_evol[key] = {"jours": 0, "nom_ressource": nom_ressource}
                cumul_hors_evol[key]["jours"] += jours
                cumul_hors_evol[key]["nom_ressource"] = nom_ressource
                nb_traites += 1
            else:
                nb_ignores += 1

        except Exception:
            logger.exception("Erreur traitement ligne ChangePoint")
            nb_erreurs += 1

    nb_crees_squelettes, codes_traites = _upsert_evolutions(db, cumul_evolutions, codes_non_reconnus)
    _upsert_hors_evolutions(db, cumul_hors_evol)

    # Snapshot auto pour chaque évolution dont les temps ont bougé
    if codes_traites:
        from services.snapshot_service import creer_snapshot_auto
        from models import Evolution
        db.flush()  # garantit que les nouveaux TempsConsomme sont visibles pour le snapshot
        for code_aha in codes_traites:
            evol = db.query(Evolution).filter(Evolution.code == code_aha).first()
            if evol:
                creer_snapshot_auto(db, evol)

    # Pas de db.commit() ici — la transaction est gérée par le routeur
    lignes_detail = []
    if codes_non_reconnus:
        lignes_detail.append("Codes évolution non reconnus / squelettes créés:\n" + "\n".join(sorted(codes_non_reconnus)))
    if time_niv2_inconnus:
        lignes_detail.append("Time_Niv2 sans mapping équipe (à configurer dans Admin):\n" + "\n".join(sorted(time_niv2_inconnus)))

    return {
        "nb_crees": nb_crees_squelettes,
        "nb_mis_a_jour": nb_traites,
        "nb_ignores": nb_ignores,
        "nb_erreurs": nb_erreurs,
        "detail": "\n\n".join(lignes_detail) if lignes_detail else None,
    }


def _upsert_evolutions(db: Session, cumul: dict, codes_non_reconnus: set) -> tuple:
    from models import Evolution, EtapeCycleVie

    nb_crees = 0
    squelettes_crees: set = set()
    codes_traites: set = set()

    for (code_aha, matricule, annee, mois), data in cumul.items():
        evol = db.query(Evolution).filter(Evolution.code == code_aha).first()

        if not evol and code_aha not in squelettes_crees:
            code_equipe = data.get("code_equipe")
            if not code_equipe:
                codes_non_reconnus.add(
                    f"{code_aha} (ignoré — équipe inconnue, configurer le mapping Time_Niv2)"
                )
                continue

            sp = db.begin_nested()
            try:
                evol = Evolution(
                    code=code_aha,
                    libelle=code_aha,
                    code_equipe=code_equipe,
                    statut_aha="Non importé Aha",
                    active=True,
                )
                db.add(evol)
                db.flush()
                for etape_val in _ETAPES_VALEURS:
                    db.add(EtapeCycleVie(
                        evolution_code=code_aha,
                        etape=etape_val,
                        statut=_STATUT_A_FAIRE,
                        pourcentage_avancement=0,
                    ))
                db.flush()
                sp.commit()
                squelettes_crees.add(code_aha)
                nb_crees += 1
                codes_non_reconnus.add(f"{code_aha} (squelette créé — import Aha requis)")
            except Exception as e:
                sp.rollback()
                codes_non_reconnus.add(f"{code_aha} (erreur création squelette : {e})")
                continue

        if not evol:
            evol = db.query(Evolution).filter(Evolution.code == code_aha).first()
            if not evol:
                continue

        existing = db.query(TempsConsomme).filter_by(
            evolution_code=code_aha, matricule=matricule, annee=annee, mois=mois
        ).first()

        if existing:
            existing.jours = data["jours"]
            existing.nom_ressource = data["nom_ressource"]
            existing.code_equipe = data["code_equipe"]
            existing.type_equipe = data["type_equipe"]
        else:
            db.add(TempsConsomme(
                evolution_code=code_aha,
                matricule=matricule,
                nom_ressource=data["nom_ressource"],
                code_equipe=data["code_equipe"],
                type_equipe=data["type_equipe"],
                annee=annee,
                mois=mois,
                jours=data["jours"],
            ))
        codes_traites.add(code_aha)

    return nb_crees, codes_traites


def _upsert_hors_evolutions(db: Session, cumul: dict):
    for (time_niv2, nom_tache, matricule, annee, mois), data in cumul.items():
        existing = db.query(TacheHorsEvolution).filter_by(
            time_niv2=time_niv2, nom_tache=nom_tache, matricule=matricule, annee=annee, mois=mois
        ).first()
        if existing:
            existing.jours = data["jours"]
            existing.nom_ressource = data["nom_ressource"]
        else:
            db.add(TacheHorsEvolution(
                time_niv2=time_niv2,
                nom_tache=nom_tache,
                matricule=matricule,
                nom_ressource=data["nom_ressource"],
                annee=annee,
                mois=mois,
                jours=data["jours"],
            ))
