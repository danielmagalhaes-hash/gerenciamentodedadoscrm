"""Modelos Pydantic para inscritos WPP Fluxo (CSV Vekta/Alia)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class WppFlowSubscriberRow(BaseModel):
    data:          Optional[date] = None
    email:         Optional[str]  = None
    telefone:      str
    alia_campanha: str
    vekta_status:  Optional[str]  = None
    vekta_detalhe: Optional[str]  = None

    @field_validator("telefone", mode="before")
    @classmethod
    def strip_telefone(cls, v: object) -> str:
        val = str(v).strip() if v is not None else ""
        if not val:
            raise ValueError(f"Telefone vazio: recebido '{v}'")
        return val

    @field_validator("alia_campanha", mode="before")
    @classmethod
    def normalize_alia(cls, v: object) -> str:
        val = str(v).strip().lower() if v is not None else ""
        if not val:
            raise ValueError(f"Alia campanha vazia: recebido '{v}'")
        return val

    @field_validator("data", mode="before")
    @classmethod
    def parse_data(cls, v: object) -> Optional[date]:
        if not v:
            return None
        from datetime import datetime as _dt
        s = str(v).strip()
        # Tenta formatos com e sem hora
        for fmt in ("%d/%m/%Y, %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
            try:
                return _dt.strptime(s, fmt).date()
            except ValueError:
                continue
        return None
