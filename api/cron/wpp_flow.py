"""Cron: ingere inscritos WPP Fluxo do CSV a cada hora."""
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


@app.route('/api/cron/wpp_flow', methods=['GET'])
def wpp_flow():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.sources.wpp_flow_subscribers import run_wpp_flow_subscribers_ingestion
        total = run_wpp_flow_subscribers_ingestion()
        from ingestion.alert import log_cron
        log_cron('wpp_flow', 'ok')
        return jsonify({'status': 'ok', 'job': 'wpp_flow', 'rows': total})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'wpp_flow', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('wpp_flow', str(e))
        return jsonify({'error': str(e)}), 500
