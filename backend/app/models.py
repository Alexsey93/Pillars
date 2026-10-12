from datetime import datetime, timezone
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

from app.regions import Region


class Material(str, Enum):
    REINFORCED_CONCRETE = "Железобетон"
    WOOD = "Дерево"
    METAL = "Металл"
    COMPOSITE = "Композит"
    OTHER = "Другое"


class ClassVoltage(str, Enum):
    V_0_4 = "0.4 кВ"
    V_6 = "6 кВ"
    V_10 = "10 кВ"
    V_35 = "35 кВ"
    V_110 = "110 кВ"
    V_220 = "220 кВ"
    OTHER = "Другое"


class Registry(SQLModel, table=True):
    """Реестр опор по одной улице."""
    id: int | None = Field(default=None, primary_key=True)

    region: Region = Field(index=True)
    raion: str | None = Field(default=None, index=True)
    city: str | None = Field(default=None, index=True)
    street: str = Field(index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)

    pillars: list["Pillar"] = Relationship(back_populates="registry_obj")


class Pillar(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    registry_id: int = Field(foreign_key="registry.id", index=True)
    registry_obj: Registry | None = Relationship(back_populates="pillars")

    # Координаты
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    # Владелец и учёт
    owner: str | None = Field(default=None)
    number_owner_pilar: str | None = Field(default=None)

    # Характеристики опоры
    material: Material | None = Field(default=None)
    height: float | None = Field(default=None, ge=0, le=200)
    class_voltage: ClassVoltage | None = Field(default=None)

    # Подвесы и кабели Ростелеком
    cnt_fastening: int = Field(default=0, ge=0)
    cnt_vok_not_ab: int = Field(default=0, ge=0)
    cnt_mzhk_not_ab: int = Field(default=0, ge=0)
    cnt_ab_vok_mzhk: int = Field(default=0, ge=0)

    # Оборудование Ростелеком
    cnt_o_coup: int = Field(default=0, ge=0)
    cnt_vols_upmk: int = Field(default=0, ge=0)
    cnt_m_coup: int = Field(default=0, ge=0)
    cnt_mzhk_upmk: int = Field(default=0, ge=0)
    cnt_shk: int = Field(default=0, ge=0)
    cnt_ork: int = Field(default=0, ge=0)
    cnt_rk: int = Field(default=0, ge=0)
    cnt_out_on_earth: int = Field(default=0, ge=0)

    # Служебные
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)