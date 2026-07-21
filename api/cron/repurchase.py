"""Cron: recarrega fact_repurchase_deals (source='sheets_diario') a partir da
planilha "Base de Dados", uma vez por dia, de madrugada."""
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


@app.route('/api/cron/repurchase', methods=['GET'])
def repurchase():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.main_repurchase_deals import run_repurchase_deals_diario
        result = run_repurchase_deals_diario()
        from ingestion.alert import log_cron
        log_cron('repurchase', 'ok')
        return jsonify({'status': 'ok', 'job': 'repurchase', **result})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'repurchase', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('repurchase', str(e))
        return jsonify({'error': str(e)}), 500
