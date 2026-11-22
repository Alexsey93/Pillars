from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import uuid

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SAEnum, Numeric, ForeignKey
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID

from app.regions import Region
from app.database import Base


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


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Пользователь. Поле email хранит username."""
    __tablename__ = "user"
    pass


class Registry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: uuid.UUID = Field(
        sa_column=Column(
            GUID(),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    region: Region = Field(
        sa_column=Column(
            SAEnum(
                Region,
                native_enum=False,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=False,
            index=True,
        )
    )

    raion: str | None = Field(default=None, index=True)
    city: str | None = Field(default=None, index=True)
    street: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)
    pillars: list["Pillar"] = Relationship(
        back_populates="registry_obj",
        cascade_delete=True,      # ← SQLModel-параметр, не "cascade"
        passive_deletes=True,
    )


class Pillar(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # Глобальный ID
    registry_id: int = Field(
        foreign_key="registry.id",
        index=True,
        ondelete="CASCADE",
    )
    registry_obj: Registry | None = Relationship(back_populates="pillars")

    house_number: str | None = Field(default=None, max_length=50)
    latitude: Decimal | None = Field(default=None, sa_column=Column(Numeric(9, 6), nullable=True))
    longitude: Decimal | None = Field(default=None, sa_column=Column(Numeric(9, 6), nullable=True))
    owner: str | None = Field(default=None)
    number_owner_pilar: str | None = Field(default=None)

    material: Material | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                Material,
                native_enum=False,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=True,
        ),
    )
    height: float | None = Field(default=None, ge=0, le=200)
    class_voltage: ClassVoltage | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                ClassVoltage,
                native_enum=False,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=True,
        ),
    )

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

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)


class DownloadToken(SQLModel, table=True):
    """Одноразовый токен для скачивания файла."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    token: str = Field(index=True, unique=True)
    registry_id: int = Field(foreign_key="registry.id", ondelete="CASCADE")
    user_id: uuid.UUID = Field(
        sa_column=Column(
            GUID(),
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    expires_at: datetime
    used: bool = Field(default=False)