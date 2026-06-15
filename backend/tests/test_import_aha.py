import pytest
from services.import_aha import import_aha
from models import Evolution, EtapeCycleVie, WorkspaceMapping, Release, Equipe


def csv_bytes(*rows):
    header = (
        "Master feature reference #,Master feature name,Workspace name,"
        "Release name,Master feature status,Master feature initial estimate,"
        "Type évolution,To-do due date"
    )
    return "\n".join([header, *rows]).encode("utf-8")


@pytest.fixture
def setup_equipe_ws(db):
    equipe = Equipe(code="EQ01", libelle="Équipe 1", type_equipe="DEV")
    mapping = WorkspaceMapping(workspace_aha="WS_TEST", code_equipe="EQ01")
    db.add_all([equipe, mapping])
    db.flush()


class TestImportAha:
    def test_empty_bytes_returns_erreur(self, db):
        result = import_aha(db, b"", "test.csv")
        assert result["nb_erreurs"] >= 1

    def test_unknown_workspace_ignores_row(self, db):
        csv = csv_bytes("ASD-E-001,Mon évolution,Workspace Inconnu,,En cours,,,")
        result = import_aha(db, csv, "test.csv")
        assert result["nb_ignores"] >= 1
        assert result["nb_crees"] == 0

    def test_creates_evolution_and_7_etapes(self, db, setup_equipe_ws):
        csv = csv_bytes("ASD-E-001,Mon évolution,WS_TEST,,En cours,10,,")
        result = import_aha(db, csv, "test.csv")

        assert result["nb_crees"] == 1
        assert result["nb_erreurs"] == 0

        evol = db.query(Evolution).filter_by(code="ASD-E-001").first()
        assert evol is not None
        assert evol.libelle == "Mon évolution"
        assert evol.budget == 10.0
        assert evol.active is True
        etapes = db.query(EtapeCycleVie).filter_by(evolution_code="ASD-E-001").all()
        assert len(etapes) == 7

    def test_updates_existing_evolution(self, db, setup_equipe_ws):
        evol = Evolution(
            code="ASD-E-002",
            libelle="Ancien libellé",
            code_equipe="EQ01",
            statut_aha="Idée",
            active=True,
        )
        db.add(evol)
        db.flush()

        csv = csv_bytes("ASD-E-002,Nouveau libellé,WS_TEST,,En cours,15,,")
        result = import_aha(db, csv, "test.csv")

        assert result["nb_mis_a_jour"] == 1
        assert result["nb_crees"] == 0
        db.flush()
        db.refresh(evol)
        assert evol.libelle == "Nouveau libellé"
        assert evol.statut_aha == "En cours"
        assert evol.budget == 15.0

    def test_diff_ajout_pour_nouvelle_evolution_avec_release(self, db, setup_equipe_ws):
        release = Release(
            code="REL01", libelle="Release 1", version="8.21", mois=3, annee=2025
        )
        db.add(release)
        db.flush()

        csv = csv_bytes("ASD-E-003,Évolution 1,WS_TEST,Release 1,En cours,10,,")
        result = import_aha(db, csv, "test.csv")

        ajouts = [d for d in result.get("diffs", []) if d["type_diff"] == "AJOUT"]
        assert len(ajouts) == 1
        assert ajouts[0]["evolution_code"] == "ASD-E-003"
        assert ajouts[0]["code_release"] == "REL01"

    def test_abandonnee_sets_active_false(self, db, setup_equipe_ws):
        csv = csv_bytes("ASD-E-004,À abandonner,WS_TEST,,Abandonnée,,,")
        import_aha(db, csv, "test.csv")

        evol = db.query(Evolution).filter_by(code="ASD-E-004").first()
        assert evol is not None
        assert evol.active is False

    def test_diff_changement_statut_pour_evolution_existante(self, db, setup_equipe_ws):
        release = Release(
            code="REL02", libelle="Release 2", version="8.22", mois=5, annee=2025
        )
        evol = Evolution(
            code="ASD-E-005",
            libelle="Évolution 5",
            code_equipe="EQ01",
            code_release="REL02",
            statut_aha="Idée",
            active=True,
        )
        db.add_all([release, evol])
        db.flush()

        csv = csv_bytes("ASD-E-005,Évolution 5,WS_TEST,Release 2,En cours,5,,")
        result = import_aha(db, csv, "test.csv")

        changements = [d for d in result.get("diffs", []) if d["type_diff"] == "CHANGEMENT_STATUT"]
        assert len(changements) == 1
        assert changements[0]["ancienne_valeur"] == "Idée"
        assert changements[0]["nouvelle_valeur"] == "En cours"
