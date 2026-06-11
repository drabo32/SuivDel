import csv
import io
import re
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from models import Evolution, EtapeCycleVie

CODE_AHA_RE = re.compile(r'^[A-Z]+-E-\d+$')


def _decoder(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("latin-1", errors="replace")


def _normalize(s: str) -> str:
    """Remplace les sauts de ligne, collapse les espaces multiples, strip."""
    return " ".join(s.replace("\n", " ").split())


def _find_col(header: list, *names: str):
    """Recherche un index de colonne par nom exact (insensible à la casse)."""
    for name in names:
        for i, h in enumerate(header):
            if _normalize(h).lower() == name.lower():
                return i
    return None


def _parse_float(val: str):
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


def _parse_date(val: str):
    if not val or not val.strip():
        return None
    val = val.strip()
    # Numéro de série Excel (ex: 45881)
    try:
        serial = int(val)
        if serial > 1000:
            return (datetime(1899, 12, 30) + timedelta(days=serial)).date()
    except ValueError:
        pass
    # Format DD/MM/YYYY
    try:
        return datetime.strptime(val, "%d/%m/%Y").date()
    except ValueError:
        pass
    # Format YYYY-MM-DD
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        pass
    return None


def import_init(db: Session, content: bytes, nom_fichier: str) -> dict:
    nb_maj = nb_ignores = nb_erreurs = 0
    details = []

    texte = _decoder(content)
    reader = csv.reader(io.StringIO(texte), delimiter=";")

    # La première ligne est l'en-tête (peut s'étaler sur plusieurs lignes physiques
    # à cause des champs multi-lignes entre guillemets — csv.reader gère ça)
    try:
        header_raw = next(reader)
    except StopIteration:
        return {"nb_crees": 0, "nb_mis_a_jour": 0, "nb_ignores": 0, "nb_erreurs": 1,
                "detail": "Fichier vide"}

    header = [_normalize(h) for h in header_raw]

    # Localisation des colonnes
    idx_code         = _find_col(header, "Ref. Aha Master feature")
    idx_macro        = _find_col(header, "Macro Chiffrage")
    idx_chiffrage_ed = _find_col(header, "Chiffrage Edition")
    idx_raf_dev      = _find_col(header, "RAF DEV M")
    idx_raf_cvg      = _find_col(header, "RAF CVG M")
    idx_conso_2025   = _find_col(header, "Conso 2025")
    # Colonnes étapes
    idx_date_pm      = _find_col(header, "date prévisionnelle presentation fiche initiatitive (PM)",
                                         "date prévisionnelle presentation fiche initiative (PM)")
    idx_date_po      = _find_col(header, "date prévisionnelle fin instruction PO")
    idx_resp_po      = _find_col(header, "PO/PPO")
    idx_date_ppo     = _find_col(header, "date prévisionnelle fin instruction PPO")
    idx_pct_recette  = _find_col(header, "% R7 Intégra.tion", "% R7 Intégration", "%  R7 Intégra.tion")
    idx_date_livr    = _find_col(header, "date previsionnelle mise à dispo CVG",
                                         "date prévisionnelle mise à dispo CVG")
    idx_date_livr_r  = _find_col(header, "date réelle mise à dispo  V8", "date réelle mise à dispo V8")
    idx_pct_testing  = _find_col(header, "% Recette CVG V8", "% Recette CVG  V8")
    idx_resp_testing = _find_col(header, "Testeur CVG")
    idx_com_testing  = _find_col(header, "Charge estimée (S, M, L, XL)")

    if idx_code is None:
        return {
            "nb_crees": 0, "nb_mis_a_jour": 0, "nb_ignores": 0, "nb_erreurs": 1,
            "detail": (
                f"Colonne 'Ref. Aha Master feature' introuvable.\n"
                f"Colonnes détectées : {header[:15]}"
            ),
        }

    colonnes_manquantes = [
        nom for nom, idx in [
            ("Macro Chiffrage", idx_macro),
            ("Chiffrage Edition", idx_chiffrage_ed),
            ("RAF DEV M", idx_raf_dev),
            ("RAF CVG M", idx_raf_cvg),
            ("Conso 2025", idx_conso_2025),
            ("date prévisionnelle PM", idx_date_pm),
            ("date prévisionnelle fin PO", idx_date_po),
            ("PO/PPO (responsable)", idx_resp_po),
            ("date prévisionnelle fin PPO", idx_date_ppo),
            ("% Recette interne", idx_pct_recette),
            ("date prévisionnelle Livraison", idx_date_livr),
            ("date réelle Livraison", idx_date_livr_r),
            ("% Recette Pôle Testing", idx_pct_testing),
            ("Testeur CVG (responsable)", idx_resp_testing),
            ("Charge estimée (commentaire testing)", idx_com_testing),
        ] if idx is None
    ]
    if colonnes_manquantes:
        details.append(f"Colonnes non trouvées (ignorées) : {', '.join(colonnes_manquantes)}")

    def get(row, idx):
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    for row in reader:
        code = get(row, idx_code)
        if not CODE_AHA_RE.match(code):
            nb_ignores += 1
            continue

        evolution = db.query(Evolution).filter(Evolution.code == code).first()
        if not evolution:
            nb_ignores += 1
            details.append(f"non trouvée en base : {code}")
            continue

        try:
            macro        = _parse_float(get(row, idx_macro))
            chiffrage_ed = _parse_float(get(row, idx_chiffrage_ed))
            raf_dev      = _parse_float(get(row, idx_raf_dev))
            raf_cvg      = _parse_float(get(row, idx_raf_cvg))
            conso_2025   = _parse_float(get(row, idx_conso_2025))
            date_pm      = _parse_date(get(row, idx_date_pm))
            date_po      = _parse_date(get(row, idx_date_po))
            resp_po      = get(row, idx_resp_po) or None
            date_ppo     = _parse_date(get(row, idx_date_ppo))
            pct_recette  = _parse_float(get(row, idx_pct_recette))
            date_livr    = _parse_date(get(row, idx_date_livr))
            date_livr_r  = _parse_date(get(row, idx_date_livr_r))
            pct_testing  = _parse_float(get(row, idx_pct_testing))
            resp_testing = get(row, idx_resp_testing) or None
            com_testing  = get(row, idx_com_testing) or None

            modifie = False
            chiffrage_modifie = False

            # Champs évolution
            if macro is not None:
                evolution.macro_chiffrage = macro
                modifie = True
                chiffrage_modifie = True
            if chiffrage_ed is not None:
                evolution.chiffrage_edition = chiffrage_ed
                modifie = True
                chiffrage_modifie = True
            if raf_dev is not None:
                evolution.raf_dev = raf_dev
                modifie = True
                chiffrage_modifie = True
            if raf_cvg is not None:
                evolution.raf_testing = raf_cvg
                modifie = True
                chiffrage_modifie = True
            if conso_2025 is not None:
                evolution.conso_2025 = conso_2025
                modifie = True

            # Champs étapes — etape_nom → {champ: valeur}
            # pourcentage_avancement : valeur float du CSV (ex: 14,2 → 14%) → arrondi en int
            etapes_updates = {
                "Analyse PM":            {"date_prevue": date_pm},
                "Analyse PO":            {"date_prevue": date_po, "responsable": resp_po},
                "Analyse PPO":           {"date_prevue": date_ppo},
                "Recette interne":       {"pourcentage_avancement": min(100, round(pct_recette * 100)) if pct_recette is not None else None},
                "Livraison intégration": {"date_prevue": date_livr, "date_reelle": date_livr_r},
                "Recette Pôle Testing":  {
                    "pourcentage_avancement": min(100, round(pct_testing * 100)) if pct_testing is not None else None,
                    "responsable": resp_testing,
                    "commentaire": com_testing,
                },
            }
            etapes_map = {et.etape.value: et for et in evolution.etapes}

            for nom_etape, champs in etapes_updates.items():
                etape_obj = etapes_map.get(nom_etape)
                if etape_obj is None:
                    continue
                for champ, valeur in champs.items():
                    if valeur is not None:
                        setattr(etape_obj, champ, valeur)
                        modifie = True
                # Règle statut selon le type d'étape
                if nom_etape == "Livraison intégration":
                    etape_obj.statut = "Terminé" if etape_obj.date_reelle else "À faire"
                else:
                    pct = etape_obj.pourcentage_avancement or 0
                    if pct == 0:
                        etape_obj.statut = "À faire"
                    elif pct == 100:
                        etape_obj.statut = "Terminé"
                    else:
                        etape_obj.statut = "En cours"

            if modifie:
                if chiffrage_modifie:
                    from services.snapshot_service import creer_snapshot_auto
                    creer_snapshot_auto(db, evolution)
                nb_maj += 1
            else:
                nb_ignores += 1

        except Exception as e:
            nb_erreurs += 1
            details.append(f"erreur {code} : {e}")

    db.commit()

    return {
        "nb_crees": 0,
        "nb_mis_a_jour": nb_maj,
        "nb_ignores": nb_ignores,
        "nb_erreurs": nb_erreurs,
        "detail": "\n".join(details) if details else None,
    }
