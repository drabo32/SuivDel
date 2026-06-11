import csv
import io
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from models import Evolution, Release, WorkspaceMapping, EtapeCycleVie

# Valeurs brutes correspondant aux enums PostgreSQL — on évite tout objet enum Python
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

STATUTS_INACTIFS = {"Abandonnée"}


def _parse_date(val: str):
    if not val or not val.strip():
        return None
    val = val.strip()
    # Numéro de série Excel
    try:
        serial = int(val)
        if serial > 1000:
            return (datetime(1899, 12, 30) + timedelta(days=serial)).date()
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            pass
    return None


def _decoder(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, ValueError):
            continue
    return content.decode("latin-1", errors="replace")


def import_aha(db: Session, content: bytes, nom_fichier: str) -> dict:
    nb_crees = nb_maj = nb_ignores = nb_erreurs = 0
    codes_non_reconnus = []
    diffs = []

    workspace_map = {m.workspace_aha: m.code_equipe for m in db.query(WorkspaceMapping).all()}
    releases = db.query(Release).all()

    try:
        texte = _decoder(content)
    except Exception as e:
        return {
            "nb_crees": 0, "nb_mis_a_jour": 0, "nb_ignores": 0, "nb_erreurs": 1,
            "detail": f"Impossible de décoder le fichier : {e}",
            "diffs": [],
        }

    # Détection automatique du séparateur (; ou ,)
    sample = texte[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"

    reader = csv.DictReader(io.StringIO(texte), delimiter=delimiter)

    for row in reader:
        code = ""
        try:
            code = (row.get("Master feature reference #") or "").strip()
            if not code:
                nb_ignores += 1
                continue

            workspace = (row.get("Workspace name") or "").strip()
            code_equipe = workspace_map.get(workspace)
            if not code_equipe:
                nb_ignores += 1
                codes_non_reconnus.append(f"workspace inconnu: {workspace}")
                continue

            release_libelle = (row.get("Release name") or "").strip()
            release_libelle_low = release_libelle.lower()
            code_release = None
            for r in releases:
                if (r.version.lower() in release_libelle_low
                        or r.libelle.lower() in release_libelle_low
                        or release_libelle_low in r.libelle.lower()):
                    code_release = r.code
                    break
            if release_libelle and not code_release:
                codes_non_reconnus.append(f"release non trouvée: '{release_libelle}'")

            statut_aha = (row.get("Master feature status") or "").strip()
            active = statut_aha not in STATUTS_INACTIFS

            # "Master feature initial estimate" en priorité, sinon "Macro chiffrage"
            budget_raw = (
                row.get("Master feature initial estimate")
                or row.get("Macro chiffrage")
                or ""
            ).strip().replace(",", ".")
            budget = float(budget_raw) if budget_raw else None

            libelle = (row.get("Master feature name") or "").strip()

            evolution = db.query(Evolution).filter(Evolution.code == code).first()

            # Capturer l'état AVANT modification pour calculer les diffs
            evolution_existed = evolution is not None
            old_release = evolution.code_release if evolution else None
            old_statut = evolution.statut_aha if evolution else None

            if evolution:
                evolution.libelle = libelle
                evolution.code_equipe = code_equipe
                evolution.code_release = code_release
                evolution.type_evolution = (row.get("Type évolution") or "").strip()
                evolution.statut_aha = statut_aha
                evolution.budget = budget
                evolution.active = active
                evolution.date_import = date.today()
                # Créer les étapes si elles sont manquantes (évolutions importées avant cette fonctionnalité)
                if not evolution.etapes:
                    _creer_etapes(db, code)
                nb_maj += 1
            else:
                evolution = Evolution(
                    code=code,
                    libelle=libelle,
                    code_equipe=code_equipe,
                    code_release=code_release,
                    type_evolution=(row.get("Type évolution") or "").strip(),
                    statut_aha=statut_aha,
                    budget=budget,
                    active=active,
                    date_import=date.today(),
                )
                db.add(evolution)
                sp = db.begin_nested()
                try:
                    db.flush()
                    _creer_etapes(db, code)
                    sp.commit()
                    nb_crees += 1
                except Exception as flush_err:
                    sp.rollback()
                    db.expunge(evolution)
                    nb_erreurs += 1
                    codes_non_reconnus.append(f"erreur flush {code}: {flush_err}")
                    continue

            # --- Snapshot auto si budget modifié ---
            from services.snapshot_service import creer_snapshot_auto
            creer_snapshot_auto(db, evolution)

            # --- Mise à jour date_reelle Analyse PM ---
            todo_due_raw = (row.get("To-do due date") or "").strip()
            todo_due = _parse_date(todo_due_raw)
            if todo_due is not None:
                etape_pm = (
                    db.query(EtapeCycleVie)
                    .filter(
                        EtapeCycleVie.evolution_code == code,
                        EtapeCycleVie.etape == "Analyse PM",
                    )
                    .first()
                )
                if etape_pm:
                    etape_pm.date_reelle = todo_due
                    etape_pm.statut = "Terminé"

            # --- Calcul des diffs de release ---
            if evolution_existed:
                if old_release != code_release:
                    # L'évolution a changé de release (ou acquis/perdu une release)
                    if old_release:
                        diffs.append({
                            "code_release": old_release,
                            "evolution_code": code,
                            "libelle_evolution": libelle,
                            "type_diff": "SUPPRESSION",
                        })
                    if code_release:
                        diffs.append({
                            "code_release": code_release,
                            "evolution_code": code,
                            "libelle_evolution": libelle,
                            "type_diff": "AJOUT",
                        })
                elif code_release and old_statut != statut_aha:
                    # Même release, statut Aha a changé
                    diffs.append({
                        "code_release": code_release,
                        "evolution_code": code,
                        "libelle_evolution": libelle,
                        "type_diff": "CHANGEMENT_STATUT",
                        "ancienne_valeur": old_statut,
                        "nouvelle_valeur": statut_aha,
                    })
            else:
                # Nouvelle évolution — premier rattachement à une release
                if code_release:
                    diffs.append({
                        "code_release": code_release,
                        "evolution_code": code,
                        "libelle_evolution": libelle,
                        "type_diff": "AJOUT",
                    })

        except Exception as e:
            nb_erreurs += 1
            codes_non_reconnus.append(f"erreur ligne '{code}': {e}")

    db.commit()

    detail = "\n".join(codes_non_reconnus) if codes_non_reconnus else None
    return {
        "nb_crees": nb_crees,
        "nb_mis_a_jour": nb_maj,
        "nb_ignores": nb_ignores,
        "nb_erreurs": nb_erreurs,
        "detail": detail,
        "diffs": diffs,
    }


def _creer_etapes(db: Session, evolution_code: str):
    for etape_val in _ETAPES_VALEURS:
        db.add(EtapeCycleVie(
            evolution_code=evolution_code,
            etape=etape_val,
            statut=_STATUT_A_FAIRE,
            pourcentage_avancement=0,
        ))
