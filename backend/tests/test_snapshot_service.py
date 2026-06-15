import pytest
from services.snapshot_service import creer_snapshot_auto
from models import Evolution, TempsConsomme, SnapshotAtterrissage, Equipe, TypeEquipe


@pytest.fixture
def equipe(db):
    e = Equipe(code="EQ01", libelle="Équipe 1", type_equipe="DEV")
    db.add(e)
    db.flush()
    return e


class TestCreerSnapshotAuto:
    def test_cree_snapshot_avec_raf(self, db, equipe):
        evol = Evolution(
            code="ASD-E-001",
            libelle="Test",
            code_equipe="EQ01",
            statut_aha="En cours",
            active=True,
            raf_dev=5.0,
            raf_testing=2.0,
            budget=20.0,
        )
        db.add(evol)
        db.flush()

        creer_snapshot_auto(db, evol)

        snap = db.query(SnapshotAtterrissage).filter_by(evolution_code="ASD-E-001").first()
        assert snap is not None
        assert snap.raf_dev == 5.0
        assert snap.raf_testing == 2.0
        assert snap.raf_total == 7.0
        assert snap.budget == 20.0

    def test_snapshot_additionne_temps_consommes(self, db, equipe):
        evol = Evolution(
            code="ASD-E-002",
            libelle="Test 2",
            code_equipe="EQ01",
            statut_aha="En cours",
            active=True,
            raf_dev=0,
            raf_testing=0,
        )
        t_dev = TempsConsomme(
            evolution_code="ASD-E-002",
            matricule="M001",
            type_equipe=TypeEquipe.DEV,
            annee=2025,
            mois=1,
            jours=4.0,
        )
        t_test = TempsConsomme(
            evolution_code="ASD-E-002",
            matricule="M002",
            type_equipe=TypeEquipe.TESTING,
            annee=2025,
            mois=2,
            jours=2.0,
        )
        db.add_all([evol, t_dev, t_test])
        db.flush()

        creer_snapshot_auto(db, evol)

        snap = db.query(SnapshotAtterrissage).filter_by(evolution_code="ASD-E-002").first()
        assert snap.temps_dev_consomme == 4.0
        assert snap.temps_testing_consomme == 2.0
        assert snap.raf_total == 0.0

    def test_raf_none_traite_comme_zero(self, db, equipe):
        evol = Evolution(
            code="ASD-E-003",
            libelle="Test 3",
            code_equipe="EQ01",
            statut_aha="En cours",
            active=True,
            raf_dev=None,
            raf_testing=None,
        )
        db.add(evol)
        db.flush()

        creer_snapshot_auto(db, evol)

        snap = db.query(SnapshotAtterrissage).filter_by(evolution_code="ASD-E-003").first()
        assert snap is not None
        assert snap.raf_total == 0.0
        assert snap.raf_dev == 0.0
        assert snap.raf_testing == 0.0

    def test_plusieurs_temps_meme_type_cumules(self, db, equipe):
        evol = Evolution(
            code="ASD-E-004",
            libelle="Test 4",
            code_equipe="EQ01",
            statut_aha="En cours",
            active=True,
            raf_dev=1.0,
            raf_testing=0,
        )
        t1 = TempsConsomme(
            evolution_code="ASD-E-004", matricule="M001",
            type_equipe=TypeEquipe.DEV, annee=2025, mois=1, jours=3.0,
        )
        t2 = TempsConsomme(
            evolution_code="ASD-E-004", matricule="M002",
            type_equipe=TypeEquipe.DEV, annee=2025, mois=2, jours=2.0,
        )
        db.add_all([evol, t1, t2])
        db.flush()

        creer_snapshot_auto(db, evol)

        snap = db.query(SnapshotAtterrissage).filter_by(evolution_code="ASD-E-004").first()
        assert snap.temps_dev_consomme == 5.0
        assert snap.raf_total == 1.0
