"""Scheduler de ingestão contínua.

Intervalos automáticos:
  - Shopify (receita):  a cada 30 minutos
  - Google Sheets (sessões): a cada hora
  - Klaviyo (e-mail):   1× por dia às 03:00

Endpoint HTTP (trigger manual):
  POST /sync?token=SYNC_SECRET_TOKEN  → smart sync (só dados novos)
  GET  /health                        → healthcheck

Uso:
  python -m ingestion.scheduler
"""
import logging
import sys
import time

import schedule
from dotenv import load_dotenv

from ingestion.sync_server import start_sync_server

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _run(name: str, fn) -> None:
    logger.info({"event": "job_start", "job": name})
    try:
        fn()
        logger.info({"event": "job_done", "job": name})
    except Exception as e:
        logger.error({"event": "job_failed", "job": name, "error": str(e)})


def _shopify() -> None:
    from ingestion.main import run_shopify_ingestion
    _run("shopify", run_shopify_ingestion)


def _sheets() -> None:
    from ingestion.main import run_sheets_ingestion
    _run("sheets", run_sheets_ingestion)


def _klaviyo() -> None:
    from ingestion.main import run_klaviyo_ingestion
    _run("klaviyo", run_klaviyo_ingestion)


def _smart_sync() -> None:
    from ingestion.main import run_smart_ingestion
    _run("smart_sync", run_smart_ingestion)


# Inicia servidor HTTP para trigger manual (POST /sync)
start_sync_server(_smart_sync)

schedule.every(30).minutes.do(_shopify)
schedule.every(1).hour.do(_sheets)
schedule.every().day.at("03:00").do(_klaviyo)

logger.info("Scheduler iniciado — Shopify: 30min | Sheets: 1h | Klaviyo: 03:00 diário | Sync HTTP: ativo")

# Executa uma vez imediatamente ao subir
_shopify()
_sheets()

while True:
    schedule.run_pending()
    time.sleep(30)
