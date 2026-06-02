"""Cron: atualiza sessões (Google Sheets) → fact_sessions. Roda a cada hora."""
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


@app.route('/api/cron/sessions', methods=['GET'])
def sessions():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.main import run_sheets_ingestion
        run_sheets_ingestion()
        from ingestion.alert import log_cron
        log_cron('sessions', 'ok')
        return jsonify({'status': 'ok', 'job': 'sessions'})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'sessions', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('sessions', str(e))
        return jsonify({'error': str(e)}), 500
