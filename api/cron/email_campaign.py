"""Cron: atualiza métricas de campanhas → campaign_email_metrics. Roda às 00h30 BRT (3h30 UTC)."""
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


@app.route('/api/cron/email_campaign', methods=['GET'])
def email_campaign():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.campaign_metrics_daily import run_yesterday
        run_yesterday()
        from ingestion.alert import log_cron
        log_cron('email_campaign', 'ok')
        return jsonify({'status': 'ok', 'job': 'email_campaign'})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'email_campaign', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('email_campaign', str(e))
        return jsonify({'error': str(e)}), 500
