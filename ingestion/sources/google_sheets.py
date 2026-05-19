import csv
import io
import logging
import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import httpx

from ingestion.models.sheets_models import SessionRow, SessionUtmRow

logger = logging.getLogger(__name__)

# Mapeamento confirmado com Daniel em 2026-05-19
CHANNEL_SLUG_MAP: dict[str, str] = {
    "Email Fluxo": "email_flow",
    "Email Campanha": "email_campaign",
    "Email Care": "email_campaign",
    "Whatsapp Fluxo": "wpp_flow",
    "Whatsapp Campanha": "wpp_campaign",
    "Whatsapp": "wpp_community",
}


def _parse_source_medium(value: str) -> tuple[str, str]:
    """Extrai utm_source e utm_medium de "email / flow"."""
    parts = [p.strip() for p in value.split("/", 1)]
    return parts[0] if parts else "", parts[1] if len(parts) > 1 else ""


def fetch_sessions_and_utm(csv_url: str | None = None) -> tuple[list[SessionRow], list[SessionUtmRow]]:
    """
    Lê o CSV uma única vez e retorna:
    - SessionRow: agregado por (date, channel) para fact_sessions
    - SessionUtmRow: granular por UTM para fact_sessions_utm
    """
    url = csv_url or os.environ["GOOGLE_SHEETS_CSV_URL"]
    logger.info("sheets: buscando dados de sessão")

    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()

    # Acumuladores
    channel_totals: dict[tuple[date, str], dict] = defaultdict(
        lambda: {"sessions": 0, "add_to_cart": 0, "begin_checkout": 0, "orders": 0, "revenue_brl": Decimal("0")}
    )
    utm_totals: dict[tuple, dict] = defaultdict(
        lambda: {"sessions": 0, "add_to_cart": 0, "begin_checkout": 0, "orders": 0, "revenue_brl": Decimal("0")}
    )
    skipped = 0

    reader = csv.DictReader(io.StringIO(resp.text))
    for row in reader:
        agrupamento = row.get("agrupamento_custom_Minimal", "").strip()
        slug = CHANNEL_SLUG_MAP.get(agrupamento)
        if not slug:
            skipped += 1
            continue

        try:
            row_date = datetime.strptime(row["event_date"].strip(), "%d/%m/%Y").date()
        except ValueError:
            logger.warning({"event": "sheets_date_parse_failed", "value": row.get("event_date")})
            skipped += 1
            continue

        sessions       = int(row.get("sessoes") or 0)
        add_to_cart    = int(row.get("add_to_cart") or 0)
        begin_checkout = int(row.get("begin_checkout") or 0)
        orders         = int(row.get("purchase") or 0)

        # Formato BR: "2.286,84" → Decimal("2286.84")
        raw_revenue = row.get("revenue", "0").strip().replace(".", "").replace(",", ".")
        try:
            revenue_brl = Decimal(raw_revenue) if raw_revenue else Decimal("0")
        except InvalidOperation:
            revenue_brl = Decimal("0")

        # Agrega para fact_sessions
        key = (row_date, slug)
        channel_totals[key]["sessions"]       += sessions
        channel_totals[key]["add_to_cart"]    += add_to_cart
        channel_totals[key]["begin_checkout"] += begin_checkout
        channel_totals[key]["orders"]         += orders
        channel_totals[key]["revenue_brl"]    += revenue_brl

        # Agrega para fact_sessions_utm
        utm_source, utm_medium = _parse_source_medium(row.get("source_medium", ""))
        utm_key = (
            row_date, slug,
            utm_source,
            utm_medium,
            row.get("campaign", "").strip(),
            row.get("term", "").strip(),
            row.get("content", "").strip(),
        )
        utm_totals[utm_key]["sessions"]       += sessions
        utm_totals[utm_key]["add_to_cart"]    += add_to_cart
        utm_totals[utm_key]["begin_checkout"] += begin_checkout
        utm_totals[utm_key]["orders"]         += orders
        utm_totals[utm_key]["revenue_brl"]    += revenue_brl

    if skipped:
        logger.warning({"event": "sheets_rows_skipped", "skipped": skipped})

    session_rows = [
        SessionRow(
            date=row_date,
            channel_slug=slug,
            sessions=vals["sessions"],
            add_to_cart=vals["add_to_cart"],
            begin_checkout=vals["begin_checkout"],
            orders=vals["orders"],
            revenue_brl=vals["revenue_brl"],
        )
        for (row_date, slug), vals in channel_totals.items()
    ]

    utm_rows = [
        SessionUtmRow(
            date=row_date,
            channel_slug=slug,
            utm_source=utm_src,
            utm_medium=utm_med,
            utm_campaign=utm_camp,
            utm_term=utm_term,
            utm_content=utm_cont,
            sessions=vals["sessions"],
            add_to_cart=vals["add_to_cart"],
            begin_checkout=vals["begin_checkout"],
            orders=vals["orders"],
            revenue_brl=vals["revenue_brl"],
        )
        for (row_date, slug, utm_src, utm_med, utm_camp, utm_term, utm_cont), vals in utm_totals.items()
    ]

    logger.info({
        "event": "sessions_parsed",
        "channel_rows": len(session_rows),
        "utm_rows": len(utm_rows),
    })
    return session_rows, utm_rows


# Mantém compatibilidade com chamadas existentes
def fetch_sessions(csv_url: str | None = None) -> list[SessionRow]:
    session_rows, _ = fetch_sessions_and_utm(csv_url)
    return session_rows
