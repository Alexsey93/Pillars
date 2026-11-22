from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import field_serializer
from sqlmodel import SQLModel, Field

from app.models import Material, ClassVoltage
from app.regions import Region


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
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None


class PillarBase(SQLModel):
    registry_id: int
    house_number: str | None = Field(default=None, max_length=50)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    owner: str | None = Field(default=None, max_length=300)
    number_owner_pilar: str | None = Field(default=None, max_length=100)
    material: Material | None = None
    height: float | None = Field(default=None, ge=0, le=200)
    class_voltage: ClassVoltage | None = None

    cnt_fastening: str = Field(default="0")
    cnt_vok_not_ab: str = Field(default="0")
    cnt_mzhk_not_ab: str = Field(default="0")
    cnt_ab_vok_mzhk: str = Field(default="0")
    cnt_o_coup: str = Field(default="0")
    cnt_vols_upmk: str = Field(default="0")
    cnt_m_coup: str = Field(default="0")
    cnt_mzhk_upmk: str = Field(default="0")
    cnt_shk: str = Field(default="0")
    cnt_ork: str = Field(default="0")
    cnt_rk: str = Field(default="0")
    cnt_out_on_earth: str = Field(default="0")

    photo_url: str | None = Field(default=None, max_length=500)

    @field_serializer("latitude", "longitude")
    def _serialize_coordinates(self, v: Decimal | None) -> float | None:
        return float(v) if v is not None else None


class PillarCreate(PillarBase):
    pass


class PillarUpdate(SQLModel):
    registry_id: int | None = None
    house_number: str | None = Field(default=None, max_length=50)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    owner: str | None = Field(default=None, max_length=300)
    number_owner_pilar: str | None = Field(default=None, max_length=100)
    material: Material | None = None
    height: float | None = Field(default=None, ge=0, le=200)
    class_voltage: ClassVoltage | None = None

    cnt_fastening: str | None = None
    cnt_vok_not_ab: str | None = None
    cnt_mzhk_not_ab: str | None = None
    cnt_ab_vok_mzhk: str | None = None
    cnt_o_coup: str | None = None
    cnt_vols_upmk: str | None = None
    cnt_m_coup: str | None = None
    cnt_mzhk_upmk: str | None = None
    cnt_shk: str | None = None
    cnt_ork: str | None = None
    cnt_rk: str | None = None
    cnt_out_on_earth: str | None = None

    photo_url: str | None = Field(default=None, max_length=500)


class PillarRead(PillarBase):
    id: int
    number_in_registry: int | None = None
    created_at: datetime
    updated_at: datetime | None = None


class DownloadLinkResponse(SQLModel):
    url: str