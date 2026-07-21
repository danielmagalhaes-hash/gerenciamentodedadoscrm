"""Backfill único (não-cron): carrega o export histórico do BigQuery
(moon-ventures-data-lake.prod_silver.silver_deals_minimal, 2021-03-18 a 2026-06-30)
em fact_repurchase_deals com source='bq_historico'.

Regras (Instrução — Gerar Tabela de Coortes de Recompra):
- Mantém somente etapa_do_negocio in {"Shipped", "Negócio Fechado - Comercial"}.
- Descarta linhas sem e-mail ou sem valor.
- tipo_de_venda em branco não é descartado (~2% da fonte, quase todo fora do escopo
  Shipped/Comercial) — vira is_first_purchase=None, a transação continua contando
  para a matriz de recompra.

Uso:
    python -m ingestion.backfill.load_repurchase_deals_historico --csv <caminho> [--dry-run]
"""

import argparse
import csv
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from dotenv import load_dotenv
from pydantic import ValidationError

from ingestion.db.client import get_supabase_client
from ingestion.db.writers import replace_repurchase_deals
from ingestion.models.repurchase_deals_models import RepurchaseDealRow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

VALID_STAGES = {"Shipped", "Negócio Fechado - Comercial"}
_TIPO_TO_IS_FIRST = {"Primeira Compra": True, "Recompra": False}


def _parse_date(raw: str) -> "datetime.date | None":
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def _parse_valor(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.strip())
    except (InvalidOperation, AttributeError):
        return None


def parse_csv(path: str) -> tuple[list[RepurchaseDealRow], int, dict[str, int]]:
    rows: list[RepurchaseDealRow] = []
    skipped_reasons: dict[str, int] = {"etapa_fora_escopo": 0, "sem_email": 0, "sem_valor": 0, "data_invalida": 0, "validacao": 0}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            etapa = (raw.get("etapa_do_negocio") or "").strip()
            if etapa not in VALID_STAGES:
                skipped_reasons["etapa_fora_escopo"] += 1
                continue

            email = (raw.get("e_mail") or "").strip().lower()
            if not email:
                skipped_reasons["sem_email"] += 1
                continue

            valor = _parse_valor(raw.get("valor") or "")
            if valor is None:
                skipped_reasons["sem_valor"] += 1
                continue

            closed_at = _parse_date(raw.get("data_de_fechamento") or "")
            if closed_at is None:
                skipped_reasons["data_invalida"] += 1
                continue

            first_purchase_raw = _parse_date(raw.get("data_primeira_compra") or "")
            is_first = _TIPO_TO_IS_FIRST.get((raw.get("tipo_de_venda") or "").strip())

            try:
                rows.append(RepurchaseDealRow(
                    email=email,
                    closed_at=closed_at,
                    amount_brl=valor,
                    is_first_purchase=is_first,
                    deal_stage=etapa,
                    first_purchase_date_raw=first_purchase_raw,
                    source="bq_historico",
                ))
            except ValidationError as e:
                skipped_reasons["validacao"] += 1
                logger.warning({"event": "repurchase_deal_row_invalid", "error": str(e)})

    total_skipped = sum(skipped_reasons.values())
    return rows, total_skipped, skipped_reasons


def run(csv_path: str, dry_run: bool) -> None:
    rows, skipped, reasons = parse_csv(csv_path)
    logger.info({"event": "repurchase_deals_historico_parsed", "valid_rows": len(rows), "skipped": skipped, "reasons": reasons})
    if dry_run:
        return
    sb = get_supabase_client()
    written = replace_repurchase_deals(sb, rows, source="bq_historico")
    logger.info({"event": "repurchase_deals_historico_backfill_done", "written": written, "skipped": skipped})


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Backfill de fact_repurchase_deals (source=bq_historico) a partir do export do BigQuery")
    parser.add_argument("--csv", required=True, help="Caminho do CSV (colunas: e_mail, data_de_fechamento, valor, tipo_de_venda, etapa_do_negocio, data_primeira_compra)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run(args.csv, args.dry_run)
