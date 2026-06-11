from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from database import get_db
from models import Evolution, Release, TempsConsomme, EtapeCycleVie, SnapshotAtterrissage, TacheHorsEvolution, TimeNiv2Mapping, RafHorsEvolution, TypeEquipe, HistoriqueDiffRelease

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("/principal")
def dashboard_principal(equipe: Optional[str] = None, release: Optional[str] = None, db: Session = Depends(get_db)):
    from datetime import datetime, date
    debut_mois_courant = datetime(date.today().year, date.today().month, 1)

    q = db.query(Evolution).filter(Evolution.active == True)
    if equipe:
        q = q.filter(Evolution.code_equipe == equipe)
    if release == "HORS_RELEASE":
        q = q.filter(Evolution.code_release == None)
    elif release:
        q = q.filter(Evolution.code_release == release)
    evolutions = q.all()

    def _att_snap(snap):
        if snap is None:
            return None
        return round(
            (snap.conso_2025 or 0) + (snap.temps_dev_consomme or 0)
            + (snap.temps_testing_consomme or 0) + (snap.raf_dev or 0) + (snap.raf_testing or 0),
            2,
        )

    liste = []
    recette_interne = {"À faire": 0, "En cours": 0, "Terminé": 0}
    par_equipe_livraison: dict = {}
    par_equipe_testing: dict = {}

    for e in evolutions:
        eq = e.code_equipe
        etapes_map = {et.etape.value: et.statut.value for et in e.etapes}
        temps_dev = round(sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.DEV), 2)
        temps_testing = round(sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.TESTING), 2)
        raf_total = round((e.raf_dev or 0) + (e.raf_testing or 0), 2)
        consomme_total = round(temps_dev + temps_testing, 2)
        atterrissage = round((e.conso_2025 or 0) + temps_dev + temps_testing + (e.raf_dev or 0) + (e.raf_testing or 0), 2)
        avancement = round(consomme_total / atterrissage * 100, 1) if atterrissage > 0 else 0

        for et in e.etapes:
            etl = et.etape.value
            stv = et.statut.value
            if etl == "Recette interne":
                recette_interne[stv] = recette_interne.get(stv, 0) + 1
            if etl == "Livraison intégration":
                par_equipe_livraison.setdefault(eq, {"À faire": 0, "En cours": 0, "Terminé": 0})
                par_equipe_livraison[eq][stv] = par_equipe_livraison[eq].get(stv, 0) + 1
            if etl == "Recette Pôle Testing":
                par_equipe_testing.setdefault(eq, {"À faire": 0, "En cours": 0, "Terminé": 0})
                par_equipe_testing[eq][stv] = par_equipe_testing[eq].get(stv, 0) + 1

        # Atterrissage M-1 : dernier snapshot avant le 1er du mois courant
        snap_m1 = next(
            (s for s in sorted(e.snapshots, key=lambda s: s.date_snapshot, reverse=True)
             if s.date_snapshot < debut_mois_courant),
            None,
        )
        att_m1 = _att_snap(snap_m1)
        delta_att = round(atterrissage - att_m1, 2) if att_m1 is not None else None

        liste.append({
            "code": e.code,
            "libelle": e.libelle,
            "equipe": e.code_equipe,
            "release": e.code_release,
            "statut_aha": e.statut_aha,
            "budget": e.budget,
            "macro_chiffrage": e.macro_chiffrage,
            "chiffrage_edition": e.chiffrage_edition,
            "conso_2025": e.conso_2025,
            "temps_dev": temps_dev,
            "temps_testing": temps_testing,
            "raf_dev": e.raf_dev,
            "raf_testing": e.raf_testing,
            "raf_total": raf_total,
            "consomme_total": consomme_total,
            "atterrissage": atterrissage,
            "atterrissage_m1": att_m1,
            "delta_atterrissage": delta_att,
            "avancement_moyen": avancement,
            "etapes": etapes_map,
        })

    # Hors-évolutions (seulement si équipe sélectionnée)
    hors_evol_total = 0
    hors_evol_raf_total = 0
    evol_raf_total = round(sum((e.raf_dev or 0) + (e.raf_testing or 0) for e in evolutions), 2)
    raf_global_total = evol_raf_total
    hors_evol_taches = []

    if equipe:
        niv2_equipe = [m.time_niv2 for m in db.query(TimeNiv2Mapping).filter(TimeNiv2Mapping.code_equipe == equipe).all()]
        taches_hors = db.query(TacheHorsEvolution).filter(TacheHorsEvolution.time_niv2.in_(niv2_equipe)).all() if niv2_equipe else []
        hors_evol_total = round(sum(t.jours for t in taches_hors), 2)
        raf_hors_map = {(r.time_niv2, r.nom_tache): r.raf for r in db.query(RafHorsEvolution).filter(RafHorsEvolution.time_niv2.in_(niv2_equipe)).all()} if niv2_equipe else {}
        hors_evol_raf_total = round(sum(raf_hors_map.values()), 2)
        raf_global_total = round(evol_raf_total + hors_evol_raf_total, 2)
        groupes_hors: dict = {}
        for t in sorted(taches_hors, key=lambda x: (x.nom_tache or x.time_niv2, x.annee, x.mois)):
            gkey = f"{t.time_niv2}||{t.nom_tache or ''}"
            mois_key = f"{t.annee}-{t.mois:02d}"
            if gkey not in groupes_hors:
                groupes_hors[gkey] = {"key": gkey, "nom_tache": t.nom_tache or "", "time_niv2": t.time_niv2, "total": 0.0, "raf": raf_hors_map.get((t.time_niv2, t.nom_tache or ""), 0.0)}
            groupes_hors[gkey][mois_key] = round(groupes_hors[gkey].get(mois_key, 0) + t.jours, 2)
            groupes_hors[gkey]["total"] = round(groupes_hors[gkey]["total"] + t.jours, 2)
        hors_evol_taches = list(groupes_hors.values())

    return {
        "evolutions": liste,
        "recette_interne": recette_interne,
        "par_equipe_livraison": par_equipe_livraison,
        "par_equipe_testing": par_equipe_testing,
        "hors_evol_total": hors_evol_total,
        "hors_evol_raf_total": hors_evol_raf_total,
        "evol_raf_total": evol_raf_total,
        "raf_global_total": raf_global_total,
        "hors_evol_taches": hors_evol_taches,
    }


@router.get("/global")
def dashboard_global(
    release: Optional[str] = None,
    equipe: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Evolution).filter(Evolution.active == True)
    if release:
        q = q.filter(Evolution.code_release == release)
    if equipe:
        q = q.filter(Evolution.code_equipe == equipe)
    evolutions = q.all()

    total = len(evolutions)
    statuts_aha = {}
    for e in evolutions:
        statuts_aha[e.statut_aha] = statuts_aha.get(e.statut_aha, 0) + 1

    temps_dev_par_equipe: dict = {}
    macro_par_equipe: dict = {}
    budget_par_equipe: dict = {}
    for e in evolutions:
        eq = e.code_equipe
        dev = sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.DEV)
        temps_dev_par_equipe[eq] = round(temps_dev_par_equipe.get(eq, 0) + dev, 2)
        macro_par_equipe[eq] = round(macro_par_equipe.get(eq, 0) + (e.macro_chiffrage or 0), 2)
        budget_par_equipe[eq] = round(budget_par_equipe.get(eq, 0) + (e.budget or 0), 2)

    avancement_etapes: dict = {}
    for e in evolutions:
        for et in e.etapes:
            etape_lib = et.etape.value
            if etape_lib not in avancement_etapes:
                avancement_etapes[etape_lib] = {"À faire": 0, "En cours": 0, "Terminé": 0, "Bloqué": 0}
            avancement_etapes[etape_lib][et.statut.value] = avancement_etapes[etape_lib].get(et.statut.value, 0) + 1

    return {
        "total": total,
        "statuts_aha": statuts_aha,
        "temps_dev_par_equipe": temps_dev_par_equipe,
        "macro_par_equipe": macro_par_equipe,
        "budget_par_equipe": budget_par_equipe,
        "avancement_etapes": avancement_etapes,
    }


@router.get("/equipe/{code_equipe}")
def dashboard_equipe(code_equipe: str, release: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Evolution).filter(Evolution.active == True, Evolution.code_equipe == code_equipe)
    if release:
        q = q.filter(Evolution.code_release == release)
    evolutions = q.all()

    result = []
    for e in evolutions:
        temps_dev = round(sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.DEV), 2)
        temps_testing = round(sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.TESTING), 2)
        etapes_statut = {et.etape.value: et.statut.value for et in e.etapes}
        result.append({
            "code": e.code,
            "libelle": e.libelle,
            "statut_aha": e.statut_aha,
            "budget": e.budget,
            "macro_chiffrage": e.macro_chiffrage,
            "chiffrage_edition": e.chiffrage_edition,
            "conso_2025": e.conso_2025,
            "temps_dev": temps_dev,
            "temps_testing": temps_testing,
            "etapes": etapes_statut,
            "raf_dev": e.raf_dev,
            "raf_testing": e.raf_testing,
        })

    recette_interne = {"À faire": 0, "En cours": 0, "Terminé": 0, "Bloqué": 0}
    for e in evolutions:
        for et in e.etapes:
            if et.etape.value == "Recette interne":
                recette_interne[et.statut.value] = recette_interne.get(et.statut.value, 0) + 1

    # --- Temps hors évolutions pour cette équipe ---
    niv2_equipe = [
        m.time_niv2
        for m in db.query(TimeNiv2Mapping).filter(TimeNiv2Mapping.code_equipe == code_equipe).all()
    ]
    taches_hors = (
        db.query(TacheHorsEvolution)
        .filter(TacheHorsEvolution.time_niv2.in_(niv2_equipe))
        .all()
    ) if niv2_equipe else []

    hors_evol_total = round(sum(t.jours for t in taches_hors), 2)

    # RAF hors-évolutions pour cette équipe
    raf_hors_map = {
        (r.time_niv2, r.nom_tache): r.raf
        for r in db.query(RafHorsEvolution).filter(RafHorsEvolution.time_niv2.in_(niv2_equipe)).all()
    } if niv2_equipe else {}
    hors_evol_raf_total = round(sum(raf_hors_map.values()), 2)

    # RAF total évolutions (dev + testing)
    evol_raf_total = round(sum((e.raf_dev or 0) + (e.raf_testing or 0) for e in evolutions), 2)
    raf_global_total = round(evol_raf_total + hors_evol_raf_total, 2)

    # Pivot par tâche → mois
    groupes_hors: dict = {}
    for t in sorted(taches_hors, key=lambda x: (x.nom_tache or x.time_niv2, x.annee, x.mois)):
        gkey = f"{t.time_niv2}||{t.nom_tache or ''}"
        mois_key = f"{t.annee}-{t.mois:02d}"
        if gkey not in groupes_hors:
            raf_val = raf_hors_map.get((t.time_niv2, t.nom_tache or ""), 0.0)
            groupes_hors[gkey] = {
                "key": gkey,
                "nom_tache": t.nom_tache or "",
                "time_niv2": t.time_niv2,
                "total": 0.0,
                "raf": raf_val,
            }
        groupes_hors[gkey][mois_key] = round(groupes_hors[gkey].get(mois_key, 0) + t.jours, 2)
        groupes_hors[gkey]["total"] = round(groupes_hors[gkey]["total"] + t.jours, 2)

    return {
        "evolutions": result,
        "recette_interne": recette_interne,
        "hors_evol_total": hors_evol_total,
        "hors_evol_raf_total": hors_evol_raf_total,
        "evol_raf_total": evol_raf_total,
        "raf_global_total": raf_global_total,
        "hors_evol_taches": list(groupes_hors.values()),
    }


@router.get("/testing")
def dashboard_testing(release: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Evolution).filter(Evolution.active == True)
    if release:
        q = q.filter(Evolution.code_release == release)
    evolutions = q.all()

    evolutions_testing = []

    for e in evolutions:
        etapes_map = {et.etape.value: et for et in e.etapes}
        recette = etapes_map.get("Recette Pôle Testing")
        livraison = etapes_map.get("Livraison intégration")

        if recette and recette.statut.value in ("À faire", "En cours"):
            temps_testing = round(sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.TESTING), 2)
            evolutions_testing.append({
                "code": e.code,
                "libelle": e.libelle,
                "equipe": e.code_equipe,
                "responsable": recette.responsable,
                "statut_recette": recette.statut.value,
                "avancement": recette.pourcentage_avancement,
                "temps_testing": temps_testing,
                "raf_testing": e.raf_testing,
                "date_livr_prevue": str(livraison.date_prevue) if livraison and livraison.date_prevue else None,
                "date_livr_reelle": str(livraison.date_reelle) if livraison and livraison.date_reelle else None,
            })

    return {
        "evolutions_testing": evolutions_testing,
        "nb_total": len(evolutions_testing),
    }


@router.get("/atterrissage")
def dashboard_atterrissage(
    date1: Optional[str] = None,
    date2: Optional[str] = None,
    release: Optional[str] = None,
    equipe: Optional[str] = None,
    db: Session = Depends(get_db),
):
    from datetime import datetime
    dt1 = datetime.strptime(date1, "%Y-%m-%d") if date1 else datetime.utcnow()
    dt2 = datetime.strptime(date2, "%Y-%m-%d") if date2 else None

    releases_map = {r.code: f"{r.version} — {r.libelle}" for r in db.query(Release).all()}

    q = db.query(Evolution).filter(Evolution.active == True)
    if release:
        q = q.filter(Evolution.code_release == release)
    if equipe:
        q = q.filter(Evolution.code_equipe == equipe)
    evolutions = q.all()

    def _atterrissage(snap):
        if snap is None:
            return None
        return round(
            (snap.conso_2025 or 0)
            + (snap.temps_dev_consomme or 0)
            + (snap.temps_testing_consomme or 0)
            + (snap.raf_dev or 0)
            + (snap.raf_testing or 0),
            2,
        )

    result = []
    for e in evolutions:
        snaps = sorted(e.snapshots, key=lambda s: s.date_snapshot)

        snap1 = next((s for s in reversed(snaps) if s.date_snapshot <= dt1), None)
        snap2 = next((s for s in reversed(snaps) if dt2 and s.date_snapshot <= dt2), None) if dt2 else None

        att1 = _atterrissage(snap1)
        att2 = _atterrissage(snap2)
        delta = round(att1 - att2, 2) if (att1 is not None and att2 is not None) else None

        couleur = "vert"
        if delta is not None and delta > 5:
            couleur = "rouge"
        elif delta is not None and delta > 0:
            couleur = "orange"

        result.append({
            "code": e.code,
            "libelle": e.libelle,
            "equipe": e.code_equipe,
            "release": releases_map.get(e.code_release, e.code_release) if e.code_release else None,
            "att_date1": att1,
            "att_date2": att2,
            "delta": delta,
            "snap1_date": snap1.date_snapshot.strftime("%d/%m/%Y %H:%M") if snap1 else None,
            "snap2_date": snap2.date_snapshot.strftime("%d/%m/%Y %H:%M") if snap2 else None,
            "couleur": couleur,
        })

    return {"evolutions": result}


@router.get("/release/{code_release}")
def dashboard_release(code_release: str, db: Session = Depends(get_db)):
    evolutions = db.query(Evolution).filter(
        Evolution.active == True,
        Evolution.code_release == code_release
    ).all()

    par_etape: dict = {}
    par_equipe_livraison: dict = {}
    par_equipe_testing: dict = {}
    raf_par_equipe: dict = {}

    for e in evolutions:
        eq = e.code_equipe
        raf_par_equipe[eq] = round(raf_par_equipe.get(eq, 0) + (e.raf_dev or 0) + (e.raf_testing or 0), 2)

        for et in e.etapes:
            etape_lib = et.etape.value
            if etape_lib not in par_etape:
                par_etape[etape_lib] = {"À faire": 0, "En cours": 0, "Terminé": 0, "Bloqué": 0}
            par_etape[etape_lib][et.statut.value] = par_etape[etape_lib].get(et.statut.value, 0) + 1

            if etape_lib == "Livraison intégration":
                if eq not in par_equipe_livraison:
                    par_equipe_livraison[eq] = {"À faire": 0, "En cours": 0, "Terminé": 0, "Bloqué": 0}
                par_equipe_livraison[eq][et.statut.value] = par_equipe_livraison[eq].get(et.statut.value, 0) + 1

            if etape_lib == "Recette Pôle Testing":
                if eq not in par_equipe_testing:
                    par_equipe_testing[eq] = {"À faire": 0, "En cours": 0, "Terminé": 0, "Bloqué": 0}
                par_equipe_testing[eq][et.statut.value] = par_equipe_testing[eq].get(et.statut.value, 0) + 1

    liste = []
    for e in evolutions:
        etapes_map = {et.etape.value: et.statut.value for et in e.etapes}
        temps_dev = round(sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.DEV), 2)
        temps_testing = round(sum(t.jours for t in e.temps if t.type_equipe == TypeEquipe.TESTING), 2)
        raf_total = round((e.raf_dev or 0) + (e.raf_testing or 0), 2)
        consomme_total = round(temps_dev + temps_testing, 2)
        atterrissage = round((e.conso_2025 or 0) + temps_dev + temps_testing + (e.raf_dev or 0) + (e.raf_testing or 0), 2)
        avancement = round(consomme_total / atterrissage * 100, 1) if atterrissage > 0 else 0
        liste.append({
            "code": e.code,
            "libelle": e.libelle,
            "equipe": e.code_equipe,
            "statut_aha": e.statut_aha,
            "budget": e.budget,
            "macro_chiffrage": e.macro_chiffrage,
            "chiffrage_edition": e.chiffrage_edition,
            "raf_total": raf_total,
            "consomme_total": consomme_total,
            "atterrissage": atterrissage,
            "avancement_moyen": avancement,
            "etapes": etapes_map,
        })

    return {
        "par_etape": par_etape,
        "par_equipe_livraison": par_equipe_livraison,
        "par_equipe_testing": par_equipe_testing,
        "raf_par_equipe": raf_par_equipe,
        "evolutions": liste,
    }


@router.get("/release/{code_release}/historique")
def historique_diff_release(code_release: str, db: Session = Depends(get_db)):
    """Retourne l'historique des diffs de contenu d'une release (ajouts/suppressions/changements de statut)."""
    diffs = (
        db.query(HistoriqueDiffRelease)
        .filter(HistoriqueDiffRelease.code_release == code_release)
        .order_by(HistoriqueDiffRelease.date_import.desc(), HistoriqueDiffRelease.evolution_code)
        .all()
    )

    # Dates d'import distinctes pour le filtre frontend
    dates_import = sorted(
        {d.date_import.strftime("%Y-%m-%dT%H:%M:%S") for d in diffs},
        reverse=True,
    )

    result = [
        {
            "id": d.id,
            "id_import": d.id_import,
            "date_import": d.date_import.strftime("%Y-%m-%dT%H:%M:%S"),
            "evolution_code": d.evolution_code,
            "libelle_evolution": d.libelle_evolution,
            "type_diff": d.type_diff,
            "ancienne_valeur": d.ancienne_valeur,
            "nouvelle_valeur": d.nouvelle_valeur,
        }
        for d in diffs
    ]

    return {"diffs": result, "dates_import": dates_import}


@router.get("/hors-evolutions")
def hors_evolutions(
    annee: Optional[int] = None,
    mois: Optional[int] = None,
    equipe: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(TacheHorsEvolution)
    if annee:
        q = q.filter(TacheHorsEvolution.annee == annee)
    if mois:
        q = q.filter(TacheHorsEvolution.mois == mois)
    if equipe:
        sous_q = db.query(TimeNiv2Mapping.time_niv2).filter(TimeNiv2Mapping.code_equipe == equipe)
        q = q.filter(TacheHorsEvolution.time_niv2.in_(sous_q))

    taches = q.all()

    # RAF saisis par tâche
    raf_map = {
        (r.time_niv2, r.nom_tache): r.raf
        for r in db.query(RafHorsEvolution).all()
    }

    # Agrégation pour le graphique
    par_equipe_mois: dict = {}
    for t in taches:
        if t.time_niv2 not in par_equipe_mois:
            par_equipe_mois[t.time_niv2] = {}
        mois_key = f"{t.annee}-{t.mois:02d}"
        par_equipe_mois[t.time_niv2][mois_key] = round(
            par_equipe_mois[t.time_niv2].get(mois_key, 0) + t.jours, 2
        )

    # Tableau pivot (1 ligne = 1 tâche) avec RAF et détail collaborateurs par mois
    pivot: dict = {}
    for t in sorted(taches, key=lambda x: (x.time_niv2, x.nom_tache or "", x.annee, x.mois)):
        tkey = (t.time_niv2, t.nom_tache or "")
        mois_key = f"{t.annee}-{t.mois:02d}"
        if tkey not in pivot:
            pivot[tkey] = {
                "key": f"{t.time_niv2}|{t.nom_tache or ''}",
                "time_niv2": t.time_niv2,
                "nom_tache": t.nom_tache or "",
                "total": 0.0,
                "raf": raf_map.get(tkey, 0.0),
                "collabsByMonth": {},
            }
        pivot[tkey][mois_key] = round(pivot[tkey].get(mois_key, 0) + t.jours, 2)
        pivot[tkey]["total"] = round(pivot[tkey]["total"] + t.jours, 2)
        if t.matricule:
            pivot[tkey]["collabsByMonth"].setdefault(mois_key, []).append({
                "matricule": t.matricule,
                "nom": t.nom_ressource or t.matricule,
                "jours": t.jours,
            })

    return {"par_equipe_mois": par_equipe_mois, "tableau": list(pivot.values())}


@router.put("/hors-evolutions-raf")
def update_raf_hors_evolution(
    time_niv2: str,
    nom_tache: str = "",
    raf: float = 0,
    db: Session = Depends(get_db),
):
    existing = db.query(RafHorsEvolution).filter_by(
        time_niv2=time_niv2, nom_tache=nom_tache
    ).first()
    if existing:
        existing.raf = raf
    else:
        db.add(RafHorsEvolution(time_niv2=time_niv2, nom_tache=nom_tache, raf=raf))
    db.commit()
    return {"ok": True}


@router.get("/controle-aha")
def controle_aha(db: Session = Depends(get_db)):
    """Liste les évolutions créées automatiquement par l'import ChangePoint
    mais pas encore importées depuis Aha (statut_aha = 'Non importé Aha')."""
    evolutions = (
        db.query(Evolution)
        .filter(Evolution.statut_aha == "Non importé Aha")
        .order_by(Evolution.code_equipe, Evolution.code)
        .all()
    )

    result = []
    for e in evolutions:
        temps = e.temps
        temps_dev = round(sum(t.jours for t in temps if t.type_equipe == TypeEquipe.DEV), 2)
        temps_testing = round(sum(t.jours for t in temps if t.type_equipe == TypeEquipe.TESTING), 2)

        mois_set = sorted({f"{t.annee}-{t.mois:02d}" for t in temps})
        premier_mois = mois_set[0] if mois_set else None
        dernier_mois = mois_set[-1] if mois_set else None

        result.append({
            "code": e.code,
            "equipe": e.code_equipe,
            "temps_dev": temps_dev,
            "temps_testing": temps_testing,
            "nb_mois": len(mois_set),
            "premier_mois": premier_mois,
            "dernier_mois": dernier_mois,
        })

    return {"evolutions": result, "total": len(result)}
