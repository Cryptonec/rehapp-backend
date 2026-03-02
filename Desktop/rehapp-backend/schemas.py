from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional


# ── Auth ───────────────────────────────────────────────────────────────────

class KurumRegister(BaseModel):
    ad: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    kurum_id: int
    kurum_ad: str


class MeResponse(BaseModel):
    kurum_id: int
    kurum_ad: str
    email: str


# ── Diagnoses ──────────────────────────────────────────────────────────────

class DiagnosisOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class DiagnosisCreate(BaseModel):
    name: str


# ── Modules ────────────────────────────────────────────────────────────────

class ModuleOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class ModuleCreate(BaseModel):
    name: str


# ── Students ───────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    name: str
    dob: Optional[date] = None
    rapor_bitis: Optional[date] = None
    diagnosis_ids: list[int] = []
    module_ids: list[int] = []


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
    rapor_bitis: Optional[date] = None
    diagnosis_ids: Optional[list[int]] = None
    module_ids: Optional[list[int]] = None


class StudentOut(BaseModel):
    id: int
    name: str
    dob: Optional[date] = None
    rapor_bitis: Optional[date] = None
    diagnoses: list[DiagnosisOut] = []
    modules: list[ModuleOut] = []
    model_config = {"from_attributes": True}


# ── Saved Groups ───────────────────────────────────────────────────────────

class SavedGroupCreate(BaseModel):
    ogrenciler: str
    moduller: str
    saat: Optional[str] = None
    notlar: Optional[str] = None
    liste_adi: str = ""


class SavedGroupPatch(BaseModel):
    liste_adi: Optional[str] = None
    notlar: Optional[str] = None


class SavedGroupOut(BaseModel):
    id: int
    ogrenciler: str
    moduller: str
    saat: Optional[str] = None
    notlar: Optional[str] = None
    liste_adi: str
    created_at: datetime
    model_config = {"from_attributes": True}
