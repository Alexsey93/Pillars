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
    cnt_fastening: str = "0"
    cnt_vok_not_ab: str = "0"
    cnt_mzhk_not_ab: str = "0"
    cnt_ab_vok_mzhk: str = "0"
    cnt_o_coup: str = "0"
    cnt_vols_upmk: str = "0"
    cnt_m_coup: str = "0"
    cnt_mzhk_upmk: str = "0"
    cnt_shk: str = "0"
    cnt_ork: str = "0"
    cnt_rk: str = "0"
    cnt_out_on_earth: str = "0"
    photo_url: Optional[str] = None          # ← добавлено
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
            cnt_fastening=str(data.get("cnt_fastening") or "0"),
            cnt_vok_not_ab=str(data.get("cnt_vok_not_ab") or "0"),
            cnt_mzhk_not_ab=str(data.get("cnt_mzhk_not_ab") or "0"),
            cnt_ab_vok_mzhk=str(data.get("cnt_ab_vok_mzhk") or "0"),
            cnt_o_coup=str(data.get("cnt_o_coup") or "0"),
            cnt_vols_upmk=str(data.get("cnt_vols_upmk") or "0"),
            cnt_m_coup=str(data.get("cnt_m_coup") or "0"),
            cnt_mzhk_upmk=str(data.get("cnt_mzhk_upmk") or "0"),
            cnt_shk=str(data.get("cnt_shk") or "0"),
            cnt_ork=str(data.get("cnt_ork") or "0"),
            cnt_rk=str(data.get("cnt_rk") or "0"),
            cnt_out_on_earth=str(data.get("cnt_out_on_earth") or "0"),
            photo_url=data.get("photo_url"),       # ← добавлено
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )