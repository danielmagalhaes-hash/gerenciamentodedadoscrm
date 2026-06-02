"""Cron: atualiza receita (Shopify) → fact_orders. Roda a cada 35 minutos."""
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)


def _authorized() -> bool:
    secret = os.environ.get('CRON_SECRET', '')
    if not secret:
        return True
    return request.headers.get('Authorization', '') == f'Bearer {secret}'


@app.route('/api/cron/revenue', methods=['GET'])
def revenue():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.main import run_smart_shopify_ingestion
        run_smart_shopify_ingestion()
        from ingestion.alert import log_cron
        log_cron('revenue', 'ok')
        return jsonify({'status': 'ok', 'job': 'revenue'})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'revenue', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('revenue', str(e))
        return jsonify({'error': str(e)}), 500
