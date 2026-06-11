from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class EquipeSchema(BaseModel):
    code: str
    libelle: str
    type_equipe: str
    model_config = {"from_attributes": True}


class ReleaseSchema(BaseModel):
    code: str
    libelle: str
    version: str
    mois: int
    annee: int
    model_config = {"from_attributes": True}


class ReleaseCreate(BaseModel):
    code: str
    libelle: str
    version: str
    mois: int
    annee: int


class WorkspaceMappingSchema(BaseModel):
    workspace_aha: str
    code_equipe: str
    model_config = {"from_attributes": True}


class EtapeSchema(BaseModel):
    id: int
    evolution_code: str
    etape: str
    statut: str
    date_prevue: Optional[date]
    date_reelle: Optional[date]
    pourcentage_avancement: int
    responsable: Optional[str]
    commentaire: Optional[str]
    date_modification: Optional[datetime]
    modifie_par: Optional[str]
    version_verrou: int
    model_config = {"from_attributes": True}


class EtapeUpdate(BaseModel):
    statut: Optional[str] = None
    date_prevue: Optional[date] = None
    date_reelle: Optional[date] = None
    pourcentage_avancement: Optional[int] = None
    responsable: Optional[str] = None
    commentaire: Optional[str] = None
    modifie_par: Optional[str] = None
    version_verrou: int


class EvolutionSchema(BaseModel):
    code: str
    libelle: str
    code_equipe: str
    code_release: Optional[str]
    type_evolution: Optional[str]
    statut_aha: Optional[str]
    budget: Optional[float]
    conso_2025: Optional[float]
    macro_chiffrage: Optional[float]
    chiffrage_edition: Optional[float]
    raf_dev: Optional[float]
    raf_testing: Optional[float]
    date_fin_estimee: Optional[date]
    active: bool
    date_import: Optional[date]
    version_verrou: int
    etapes: List[EtapeSchema] = []
    model_config = {"from_attributes": True}


class EvolutionUpdate(BaseModel):
    macro_chiffrage: Optional[float] = None
    chiffrage_edition: Optional[float] = None
    raf_dev: Optional[float] = None
    raf_testing: Optional[float] = None
    date_fin_estimee: Optional[date] = None
    version_verrou: int


class EvolutionListItem(BaseModel):
    code: str
    libelle: str
    code_equipe: str
    code_release: Optional[str]
    type_evolution: Optional[str]
    statut_aha: Optional[str]
    budget: Optional[float]
    conso_2025: Optional[float]
    macro_chiffrage: Optional[float]
    chiffrage_edition: Optional[float]
    raf_dev: Optional[float]
    raf_testing: Optional[float]
    date_fin_estimee: Optional[date]
    active: bool
    temps_dev: Optional[float] = 0
    temps_testing: Optional[float] = 0
    avancement_moyen: Optional[float] = 0
    model_config = {"from_attributes": True}


class TempsConsommeSchema(BaseModel):
    evolution_code: str
    matricule: str
    nom_ressource: Optional[str]
    code_equipe: Optional[str]
    type_equipe: Optional[str]
    annee: int
    mois: int
    jours: float
    model_config = {"from_attributes": True}


class SnapshotSchema(BaseModel):
    id: int
    evolution_code: str
    annee: int
    mois: int
    raf_dev: Optional[float]
    raf_testing: Optional[float]
    raf_total: Optional[float]
    budget: Optional[float]
    macro_chiffrage: Optional[float]
    chiffrage_edition: Optional[float]
    conso_2025: Optional[float]
    temps_dev_consomme: Optional[float]
    temps_testing_consomme: Optional[float]
    date_snapshot: datetime
    model_config = {"from_attributes": True}


class RessourceSchema(BaseModel):
    matricule: str
    nom: str
    code_equipe: Optional[str]
    type_equipe: Optional[str]
    model_config = {"from_attributes": True}


class RessourceCreate(BaseModel):
    matricule: str
    nom: str
    code_equipe: Optional[str] = None
    type_equipe: Optional[str] = None


class TacheHorsEvolutionSchema(BaseModel):
    time_niv2: str
    annee: int
    mois: int
    jours: float
    model_config = {"from_attributes": True}


class HistoriqueImportSchema(BaseModel):
    id: int
    type_import: str
    nom_fichier: Optional[str]
    date_import: datetime
    nb_crees: int
    nb_mis_a_jour: int
    nb_ignores: int
    nb_erreurs: int
    detail: Optional[str]
    model_config = {"from_attributes": True}


class HistoriqueEtapeSchema(BaseModel):
    id: int
    evolution_code: str
    etape: str
    champ_modifie: str
    ancienne_valeur: Optional[str]
    nouvelle_valeur: Optional[str]
    modifie_par: Optional[str]
    date_modification: datetime
    model_config = {"from_attributes": True}
