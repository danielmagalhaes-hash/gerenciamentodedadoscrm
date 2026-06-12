"""Ingestão de inscritos WPP Fluxo a partir do CSV público da planilha Vekta/Alia."""

import csv
import io
import logging
import os
from datetime import date

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from ingestion.db.client import get_supabase_client
from ingestion.models.wpp_flow_models import WppFlowSubscriberRow

load_dotenv()
logger = logging.getLogger(__name__)

CUTOFF_DATE = date(2026, 6, 12)
BATCH_SIZE  = 500


def fetch_wpp_flow_subscribers(csv_url: str | None = None) -> list[WppFlowSubscriberRow]:
    url = csv_url or os.environ["WPP_FLOW_SUBSCRIBERS_CSV_URL"]
    logger.info({"event": "wpp_sub_fetch_start", "url": url})

    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()

    rows: list[WppFlowSubscriberRow] = []
    skipped = 0
    reader = csv.DictReader(io.StringIO(resp.text))

    for raw in reader:
        telefone = (raw.get("Telefone") or "").strip()
        alia     = (raw.get("Alia Campanha") or "").strip()
        if not telefone or not alia:
            skipped += 1
            continue

        try:
            row = WppFlowSubscriberRow.model_validate({
                "data":          raw.get("Data"),
                "email":         raw.get("E-mail"),
                "telefone":      telefone,
                "alia_campanha": alia,
                "vekta_status":  raw.get("Vekta Status"),
                "vekta_detalhe": raw.get("Vekta Detalhe"),
            })
        except ValidationError as e:
            logger.warning({"event": "wpp_sub_parse_error", "row": raw, "error": str(e)})
            skipped += 1
            continue

        if row.data is None:
            skipped += 1
            continue
        if row.data < CUTOFF_DATE:
            skipped += 1
            continue

        rows.append(row)

    logger.info({"event": "wpp_sub_fetch_done", "rows": len(rows), "skipped": skipped})
    return rows


def upsert_wpp_flow_subscribers(rows: list[WppFlowSubscriberRow]) -> int:
    if not rows:
        return 0

    # Deduplica por (telefone, alia_campanha, data) — mesma pessoa no mesmo fluxo no mesmo dia
    seen: dict[tuple[str, str, str], WppFlowSubscriberRow] = {}
    for r in rows:
        seen[(r.telefone, r.alia_campanha, r.data.isoformat())] = r  # type: ignore[union-attr]
    rows = list(seen.values())

    sb = get_supabase_client()
    records = [
        {
            "data":          r.data.isoformat() if r.data else None,
            "email":         r.email,
            "telefone":      r.telefone,
            "alia_campanha": r.alia_campanha,
            "vekta_status":  r.vekta_status,
            "vekta_detalhe": r.vekta_detalhe,
        }
        for r in rows
    ]

    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        sb.table("fact_wpp_flow_subscribers").upsert(
            batch, on_conflict="telefone,alia_campanha,data"
        ).execute()
        total += len(batch)
        logger.info({"event": "wpp_sub_upsert_batch", "batch": i // BATCH_SIZE + 1, "rows": len(batch)})

    logger.info({"event": "wpp_sub_upsert_done", "total": total})
    return total


def run_wpp_flow_subscribers_ingestion() -> int:
    rows = fetch_wpp_flow_subscribers()
    return upsert_wpp_flow_subscribers(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    total = run_wpp_flow_subscribers_ingestion()
    print(f"{total} inscritos WPP Fluxo upsertados.")
