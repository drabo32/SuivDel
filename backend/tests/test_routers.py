import pytest
from models import Equipe, Release, Evolution


class TestEvolutionsRouter:
    def test_list_evolutions_vide(self, client):
        r = client.get("/evolutions")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_evolutions_renvoie_actives_seulement(self, client, db):
        equipe = Equipe(code="EQ01", libelle="Équipe 1", type_equipe="DEV")
        active = Evolution(
            code="ASD-E-001", libelle="Active", code_equipe="EQ01",
            statut_aha="En cours", active=True,
        )
        inactive = Evolution(
            code="ASD-E-002", libelle="Inactive", code_equipe="EQ01",
            statut_aha="Abandonnée", active=False,
        )
        db.add_all([equipe, active, inactive])
        db.commit()
        db.expire_all()

        r = client.get("/evolutions")
        assert r.status_code == 200
        codes = [e["code"] for e in r.json()]
        assert "ASD-E-001" in codes
        assert "ASD-E-002" not in codes

    def test_get_evolution_introuvable(self, client):
        r = client.get("/evolutions/CODE_INEXISTANT")
        assert r.status_code == 404

    def test_update_evolution_conflit_version(self, client, db):
        equipe = Equipe(code="EQ02", libelle="Équipe 2", type_equipe="DEV")
        evol = Evolution(
            code="ASD-E-010", libelle="Test", code_equipe="EQ02",
            statut_aha="En cours", active=True, version_verrou=0,
        )
        db.add_all([equipe, evol])
        db.commit()

        r = client.put("/evolutions/ASD-E-010", json={
            "macro_chiffrage": 10.0,
            "version_verrou": 99,
        })
        assert r.status_code == 409

    def test_get_temps_evolution(self, client, db):
        equipe = Equipe(code="EQ03", libelle="Équipe 3", type_equipe="DEV")
        evol = Evolution(
            code="ASD-E-020", libelle="Test", code_equipe="EQ03",
            statut_aha="En cours", active=True,
        )
        db.add_all([equipe, evol])
        db.commit()

        r = client.get("/evolutions/ASD-E-020/temps")
        assert r.status_code == 200
        data = r.json()
        assert data["dev_total"] == 0
        assert data["testing_total"] == 0


class TestDashboardRouter:
    def test_atterrissage_date_invalide_renvoie_422(self, client):
        r = client.get("/dashboards/atterrissage?date1=pas-une-date")
        assert r.status_code == 422

    def test_atterrissage_date_valide_renvoie_200(self, client):
        r = client.get("/dashboards/atterrissage?date1=2025-01-01")
        assert r.status_code == 200

    def test_dashboard_principal_renvoie_200(self, client):
        r = client.get("/dashboards/principal")
        assert r.status_code == 200
        data = r.json()
        assert "evolutions" in data
        assert "recette_interne" in data

    def test_dashboard_principal_filtre_equipe(self, client, db):
        equipe = Equipe(code="EQ_DASH", libelle="Équipe Dash", type_equipe="DEV")
        evol = Evolution(
            code="ASD-E-030", libelle="Test", code_equipe="EQ_DASH",
            statut_aha="En cours", active=True,
        )
        db.add_all([equipe, evol])
        db.commit()

        r = client.get("/dashboards/principal?equipe=EQ_DASH")
        assert r.status_code == 200
        data = r.json()
        codes = [e["code"] for e in data["evolutions"]]
        assert "ASD-E-030" in codes


class TestAdminRouter:
    def test_get_equipes_renvoie_200(self, client):
        r = client.get("/admin/equipes")
        assert r.status_code == 200

    def test_creer_et_lister_release(self, client):
        r = client.post("/admin/releases", json={
            "code": "R2025",
            "libelle": "Release Test",
            "version": "8.25",
            "mois": 6,
            "annee": 2025,
        })
        assert r.status_code == 200

        r2 = client.get("/admin/releases")
        assert r2.status_code == 200
        codes = [rel["code"] for rel in r2.json()]
        assert "R2025" in codes

    def test_creer_release_champs_obligatoires(self, client):
        r = client.post("/admin/releases", json={"code": "R_BAD"})
        assert r.status_code == 422


class TestHealthEndpoint:
    def test_health_renvoie_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
