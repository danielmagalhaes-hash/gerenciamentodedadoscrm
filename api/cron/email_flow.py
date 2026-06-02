"""Cron: atualiza métricas de fluxos → flow_email_metrics. Roda às 4h BRT (7h UTC)."""
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


@app.route('/api/cron/email_flow', methods=['GET'])
def email_flow():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.flow_metrics_daily import run_yesterday
        run_yesterday()
        from ingestion.alert import log_cron
        log_cron('email_flow', 'ok')
        return jsonify({'status': 'ok', 'job': 'email_flow'})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'email_flow', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('email_flow', str(e))
        return jsonify({'error': str(e)}), 500
