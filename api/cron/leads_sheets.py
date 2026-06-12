"""Cron: exporta leads_webhook para Google Sheets a cada hora."""
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


@app.route('/api/cron/leads_sheets', methods=['GET'])
def leads_sheets():
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401
    try:
        from ingestion.sources.leads_sheets_export import export_leads_to_sheets
        total = export_leads_to_sheets()
        from ingestion.alert import log_cron
        log_cron('leads_sheets', 'ok')
        return jsonify({'status': 'ok', 'job': 'leads_sheets', 'rows': total})
    except Exception as e:
        logger.error({'event': 'cron_failed', 'job': 'leads_sheets', 'error': str(e)})
        from ingestion.alert import send_failure_alert
        send_failure_alert('leads_sheets', str(e))
        return jsonify({'error': str(e)}), 500
