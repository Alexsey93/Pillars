from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Registry:
    id: int
    region: str
    street: str
    raion: Optional[str] = None
    city: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Registry":
        return cls(
            id=data["id"],
            region=data["region"],
            street=data["street"],
            raion=data.get("raion"),
            city=data.get("city"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def display_name(self) -> str:
        parts = [self.region]
        if self.city:
            parts.append(self.city)
        parts.append(self.street)
        return " · ".join(parts)


@dataclass
class Pillar:
    id: int
    registry_id: int
    house_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    owner: Optional[str] = None
    number_owner_pilar: Optional[str] = None
    material: Optional[str] = None
    height: Optional[float] = None
    class_voltage: Optional[str] = None
    cnt_fastening: int = 0
    cnt_vok_not_ab: int = 0
    cnt_mzhk_not_ab: int = 0
    cnt_ab_vok_mzhk: int = 0
    cnt_o_coup: int = 0
    cnt_vols_upmk: int = 0
    cnt_m_coup: int = 0
    cnt_mzhk_upmk: int = 0
    cnt_shk: int = 0
    cnt_ork: int = 0
    cnt_rk: int = 0
    cnt_out_on_earth: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Pillar":
        return cls(
            id=data["id"],
            registry_id=data["registry_id"],
            house_number=data.get("house_number"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            owner=data.get("owner"),
            number_owner_pilar=data.get("number_owner_pilar"),
            material=data.get("material"),
            height=data.get("height"),
            class_voltage=data.get("class_voltage"),
            cnt_fastening=data.get("cnt_fastening", 0),
            cnt_vok_not_ab=data.get("cnt_vok_not_ab", 0),
            cnt_mzhk_not_ab=data.get("cnt_mzhk_not_ab", 0),
            cnt_ab_vok_mzhk=data.get("cnt_ab_vok_mzhk", 0),
            cnt_o_coup=data.get("cnt_o_coup", 0),
            cnt_vols_upmk=data.get("cnt_vols_upmk", 0),
            cnt_m_coup=data.get("cnt_m_coup", 0),
            cnt_mzhk_upmk=data.get("cnt_mzhk_upmk", 0),
            cnt_shk=data.get("cnt_shk", 0),
            cnt_ork=data.get("cnt_ork", 0),
            cnt_rk=data.get("cnt_rk", 0),
            cnt_out_on_earth=data.get("cnt_out_on_earth", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )