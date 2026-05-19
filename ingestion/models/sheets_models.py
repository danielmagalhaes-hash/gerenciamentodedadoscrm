from datetime import date
from pydantic import BaseModel


class SessionRow(BaseModel):
    date: date
    channel_slug: str
    sessions: int
    add_to_cart: int
    begin_checkout: int


class SessionUtmRow(BaseModel):
    date: date
    channel_slug: str
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    utm_term: str = ""
    utm_content: str = ""
    sessions: int
    add_to_cart: int
    begin_checkout: int
