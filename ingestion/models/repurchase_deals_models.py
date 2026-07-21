from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

DealStage = Literal["Shipped", "Negócio Fechado - Comercial"]
DealSource = Literal["bq_historico", "sheets_diario"]


class RepurchaseDealRow(BaseModel):
    email: str
    closed_at: date
    amount_brl: Decimal
    is_first_purchase: bool | None = None
    deal_stage: DealStage
    first_purchase_date_raw: date | None = None
    source: DealSource
