from datetime import datetime
from sqlmodel import SQLModel, Field

from app.models import Material, ClassVoltage
from app.regions import Region


# ============================================================
# REGISTRY
# ============================================================

class RegistryBase(SQLModel):
    region: Region
    raion: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=200)
    street: str = Field(min_length=1, max_length=300)


class RegistryCreate(RegistryBase):
    pass


class RegistryUpdate(SQLModel):
    region: Region | None = None
    raion: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=200)
    street: str | None = Field(default=None, min_length=1, max_length=300)


class RegistryRead(RegistryBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


# ============================================================
# PILLAR
# ============================================================

class PillarBase(SQLModel):
    registry_id: int
    house_number: str | None = Field(default=None, max_length=50)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    owner: str | None = Field(default=None, max_length=300)
    number_owner_pilar: str | None = Field(default=None, max_length=100)
    material: Material | None = None
    height: float | None = Field(default=None, ge=0, le=200)
    class_voltage: ClassVoltage | None = None

    cnt_fastening: int = Field(default=0, ge=0)
    cnt_vok_not_ab: int = Field(default=0, ge=0)
    cnt_mzhk_not_ab: int = Field(default=0, ge=0)
    cnt_ab_vok_mzhk: int = Field(default=0, ge=0)
    cnt_o_coup: int = Field(default=0, ge=0)
    cnt_vols_upmk: int = Field(default=0, ge=0)
    cnt_m_coup: int = Field(default=0, ge=0)
    cnt_mzhk_upmk: int = Field(default=0, ge=0)
    cnt_shk: int = Field(default=0, ge=0)
    cnt_ork: int = Field(default=0, ge=0)
    cnt_rk: int = Field(default=0, ge=0)
    cnt_out_on_earth: int = Field(default=0, ge=0)


class PillarCreate(PillarBase):
    pass


class PillarUpdate(SQLModel):
    registry_id: int | None = None
    house_number: str | None = Field(default=None, max_length=50)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    owner: str | None = Field(default=None, max_length=300)
    number_owner_pilar: str | None = Field(default=None, max_length=100)
    material: Material | None = None
    height: float | None = Field(default=None, ge=0, le=200)
    class_voltage: ClassVoltage | None = None

    cnt_fastening: int | None = Field(default=None, ge=0)
    cnt_vok_not_ab: int | None = Field(default=None, ge=0)
    cnt_mzhk_not_ab: int | None = Field(default=None, ge=0)
    cnt_ab_vok_mzhk: int | None = Field(default=None, ge=0)
    cnt_o_coup: int | None = Field(default=None, ge=0)
    cnt_vols_upmk: int | None = Field(default=None, ge=0)
    cnt_m_coup: int | None = Field(default=None, ge=0)
    cnt_mzhk_upmk: int | None = Field(default=None, ge=0)
    cnt_shk: int | None = Field(default=None, ge=0)
    cnt_ork: int | None = Field(default=None, ge=0)
    cnt_rk: int | None = Field(default=None, ge=0)
    cnt_out_on_earth: int | None = Field(default=None, ge=0)


class PillarRead(PillarBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None