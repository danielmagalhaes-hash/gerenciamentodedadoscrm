"""Cron: ingestão diária da Comunidade WhatsApp (Sendflow). Roda às 08:00 UTC (05:00 BRT)."""
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


@app.route('/api/cron/community', methods=['GET'])
def community():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.community_daily import run_yesterday
        run_yesterday()
        from ingestion.alert import log_cron
        log_cron('community', 'ok')
        return jsonify({'status': 'ok', 'job': 'community'})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'community', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('community', str(e))
        return jsonify({'error': str(e)}), 500
