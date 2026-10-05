from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field

from app.regions import Region


class Material(str, Enum):
    """Материал опоры."""
    REINFORCED_CONCRETE = "Железобетон"
    WOOD = "Дерево"
    METAL = "Металл"
    COMPOSITE = "Композит"
    OTHER = "Другое"


class ClassVoltage(str, Enum):
    """Класс напряжения ЛЭП, кВ."""
    V_0_4 = "0.4 кВ"
    V_6 = "6 кВ"
    V_10 = "10 кВ"
    V_35 = "35 кВ"
    V_110 = "110 кВ"
    V_220 = "220 кВ"
    OTHER = "Другое"


class Pillar(SQLModel, table=True):
    """Опора ЛЭП с кабелями Ростелеком."""

    id: int | None = Field(default=None, primary_key=True)

    # --- Локация ---
    region: Region = Field(index=True)
    raion: str | None = Field(default=None, index=True)
    city: str | None = Field(default=None, index=True)
    address: str | None = Field(default=None)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    # --- Владелец и учёт ---
    owner: str | None = Field(default=None)
    number_owner_pilar: str | None = Field(default=None)

    # --- Характеристики опоры ---
    material: Material | None = Field(default=None)
    height: float | None = Field(default=None, ge=0, le=200)
    class_voltage: ClassVoltage | None = Field(default=None)

    # --- Подвесы и кабели Ростелеком ---
    cnt_fastening: int = Field(default=0, ge=0)
    cnt_vok_not_ab: int = Field(default=0, ge=0)
    cnt_mzhk_not_ab: int = Field(default=0, ge=0)
    cnt_ab_vok_mzhk: int = Field(default=0, ge=0)

    # --- Оборудование Ростелеком ---
    cnt_o_coup: int = Field(default=0, ge=0)
    cnt_vols_upmk: int = Field(default=0, ge=0)
    cnt_m_coup: int = Field(default=0, ge=0)
    cnt_mzhk_upmk: int = Field(default=0, ge=0)
    cnt_shk: int = Field(default=0, ge=0)
    cnt_ork: int = Field(default=0, ge=0)
    cnt_rk: int = Field(default=0, ge=0)
    cnt_out_on_earth: int = Field(default=0, ge=0)

    # --- Служебные ---
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)