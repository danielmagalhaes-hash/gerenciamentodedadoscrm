"""Exporta leads_webhook do Supabase para Google Sheets (atualização horária)."""

import logging
import os

import gspread
from dotenv import load_dotenv

from ingestion.db.client import get_supabase_client

load_dotenv()
logger = logging.getLogger(__name__)

CUTOFF_DATE = "2026-06-12"
HEADERS = ["Data", "Telefone", "Origem", "Funil", "Vendedor"]


def _get_worksheet() -> gspread.Worksheet:
    json_path = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON_PATH"]
    spreadsheet_id = os.environ["GOOGLE_SHEETS_LEADS_SPREADSHEET_ID"]
    gc = gspread.service_account(filename=json_path)
    return gc.open_by_key(spreadsheet_id).get_worksheet(0)


def export_leads_to_sheets() -> int:
    sb = get_supabase_client()

    resp = (
        sb.table("leads_webhook")
        .select("data,telefone,origem,funil,nome_do_vendedor")
        .gte("data", CUTOFF_DATE)
        .order("data", desc=True)
        .limit(10000)
        .execute()
    )
    rows = resp.data or []

    values = [HEADERS] + [
        [
            (r.get("data") or "")[:19].replace("T", " "),
            r.get("telefone") or "",
            r.get("origem") or "",
            r.get("funil") or "",
            r.get("nome_do_vendedor") or "",
        ]
        for r in rows
    ]

    ws = _get_worksheet()
    ws.clear()
    ws.update(values, "A1")

    logger.info({"event": "leads_sheets_exported", "rows": len(rows)})
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    total = export_leads_to_sheets()
    print(f"{total} leads exportados para o Sheets.")
