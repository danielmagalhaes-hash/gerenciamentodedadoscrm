"""Cron: atualiza formulários → dim_forms, fact_lead_captures. Roda às 6h BRT (9h UTC)."""
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


@app.route('/api/cron/forms', methods=['GET'])
def forms():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.main import run_forms_ingestion
        run_forms_ingestion()
        from ingestion.alert import log_cron
        log_cron('forms', 'ok')
        return jsonify({'status': 'ok', 'job': 'forms'})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'forms', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('forms', str(e))
        return jsonify({'error': str(e)}), 500
