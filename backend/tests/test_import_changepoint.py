import pytest
from services.import_changepoint import import_changepoint
from models import TempsConsomme, TacheHorsEvolution, Evolution, Equipe, TimeNiv2Mapping


def csv_bytes(*rows):
    header = "ApprovalStatus,RegularDay,Time_Niv0,Time_Niv2,Task,Matricule,ressource,TimeDate,Année,Mois"
    return "\n".join([header, *rows]).encode("utf-8")


@pytest.fixture
def setup_evol(db):
    equipe = Equipe(code="EQ01", libelle="Équipe 1", type_equipe="DEV")
    mapping = TimeNiv2Mapping(time_niv2="NIV2_1", code_equipe="EQ01", type_equipe="DEV")
    evol = Evolution(
        code="ASD-E-001",
        libelle="Évolution test",
        code_equipe="EQ01",
        statut_aha="En cours",
        active=True,
    )
    db.add_all([equipe, mapping, evol])
    db.flush()


class TestImportChangepoint:
    def test_ignore_si_non_approved(self, db):
        csv = csv_bytes("B,5,01-Dev,NIV2_1,ASD-E-001 - ma tâche,M001,Dupont,01/01/2025,2025,1")
        result = import_changepoint(db, csv, "test.csv")
        assert result["nb_ignores"] >= 1
        assert db.query(TempsConsomme).count() == 0

    def test_ignore_si_zero_jours(self, db):
        csv = csv_bytes("A,0,01-Dev,NIV2_1,ASD-E-001 - ma tâche,M001,Dupont,01/01/2025,2025,1")
        result = import_changepoint(db, csv, "test.csv")
        assert result["nb_ignores"] >= 1
        assert db.query(TempsConsomme).count() == 0

    def test_cree_temps_consomme(self, db, setup_evol):
        csv = csv_bytes("A,3,01-Dev,NIV2_1,ASD-E-001 - ma tâche,M001,Dupont,01/01/2025,2025,1")
        result = import_changepoint(db, csv, "test.csv")

        assert result["nb_mis_a_jour"] >= 1
        tc = db.query(TempsConsomme).filter_by(
            evolution_code="ASD-E-001", matricule="M001", annee=2025, mois=1
        ).first()
        assert tc is not None
        assert tc.jours == 3.0

    def test_cumule_meme_personne_meme_mois(self, db, setup_evol):
        csv = csv_bytes(
            "A,3,01-Dev,NIV2_1,ASD-E-001 - tâche A,M001,Dupont,01/01/2025,2025,1",
            "A,2,01-Dev,NIV2_1,ASD-E-001 - tâche B,M001,Dupont,15/01/2025,2025,1",
        )
        import_changepoint(db, csv, "test.csv")

        tc = db.query(TempsConsomme).filter_by(
            evolution_code="ASD-E-001", matricule="M001", annee=2025, mois=1
        ).first()
        assert tc is not None
        assert tc.jours == 5.0

    def test_cree_tache_hors_evolution_pour_edition(self, db):
        csv = csv_bytes(
            "A,2,03-Edition,NIV2_HORS,Activité de maintenance,M002,Martin,01/02/2025,2025,2"
        )
        import_changepoint(db, csv, "test.csv")

        tache = db.query(TacheHorsEvolution).filter_by(
            time_niv2="NIV2_HORS", annee=2025, mois=2
        ).first()
        assert tache is not None
        assert tache.jours == 2.0
        assert tache.nom_tache == "Activité de maintenance"

    def test_cree_squelette_evolution_inconnue(self, db):
        equipe = Equipe(code="EQ99", libelle="Équipe 99", type_equipe="DEV")
        mapping = TimeNiv2Mapping(time_niv2="NIV2_99", code_equipe="EQ99", type_equipe="DEV")
        db.add_all([equipe, mapping])
        db.flush()

        csv = csv_bytes("A,5,01-Dev,NIV2_99,NEW-E-999 - nouvelle évolution,M001,Dupont,01/03/2025,2025,3")
        result = import_changepoint(db, csv, "test.csv")

        assert result["nb_crees"] >= 1
        evol = db.query(Evolution).filter_by(code="NEW-E-999").first()
        assert evol is not None
        assert evol.statut_aha == "Non importé Aha"

    def test_ignore_ligne_sans_code_aha_ni_edition(self, db):
        csv = csv_bytes("A,4,01-Dev,NIV2_AUTRE,Réunion hebdo,M003,Durand,01/01/2025,2025,1")
        result = import_changepoint(db, csv, "test.csv")
        assert result["nb_ignores"] >= 1
