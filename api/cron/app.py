"""App Flask unificado para todos os cron jobs — novo runtime Vercel."""
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import jwt
from flask import Flask, jsonify, make_response, redirect, request
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
_ALLOWED_DOMAINS = ('@minimalclub.com.br', '@moonventures.com.br')
_SUPABASE_URL    = 'https://aczvusdzfrmborvvfqib.supabase.co'
_SUPABASE_ANON   = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjenZ1c2R6ZnJtYm9ydnZmcWliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg3ODkwNTIsImV4cCI6MjA5NDM2NTA1Mn0.hb0RjoXdmHN7wKLvhRCkJjq-ycqxE3FaJlYKtMEqumk'


def _get_auth_email() -> str | None:
    """Verifica o JWT Supabase no cookie e retorna o e-mail se autorizado."""
    token = request.cookies.get('sb_token', '')
    if not token:
        return None
    secret = os.environ.get('SUPABASE_JWT_SECRET', '')
    if not secret:
        return 'dev@minimalclub.com.br'  # dev sem secret configurado
    try:
        payload = jwt.decode(
            token, secret, algorithms=['HS256'],
            audience='authenticated',
            options={'verify_exp': True},
        )
        email = payload.get('email', '')
        if any(email.endswith(d) for d in _ALLOWED_DOMAINS):
            return email
        return None
    except Exception:
        return None


_LOGIN_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Dashboard CRM · Acesso</title>
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:system-ui,sans-serif;background:#f4f6fa;display:flex;align-items:center;justify-content:center;min-height:100vh}}
    .card{{background:#fff;padding:40px;border-radius:14px;box-shadow:0 2px 20px rgba(0,0,0,.08);text-align:center;width:340px}}
    h2{{font-size:20px;margin-bottom:6px;color:#111}}
    p{{color:#6b7785;font-size:14px;margin-bottom:28px}}
    .logo{{font-size:28px;margin-bottom:20px}}
    button{{width:100%;padding:13px;background:#111;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px}}
    button:hover{{background:#333}}
    .err{{color:#dc2626;font-size:13px;margin-top:14px}}
  </style>
</head>
<body>
<div class="card">
  <div class="logo">📊</div>
  <h2>Dashboard CRM</h2>
  <p>Acesso restrito a @minimalclub.com.br<br>e @moonventures.com.br</p>
  <button id="btn">
    <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#fff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#fff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#fff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#fff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
    Entrar com Google
  </button>
  <div id="err" class="err"></div>
</div>
<script>
const {{createClient}} = supabase;
const _sb = createClient('{_SUPABASE_URL}', '{_SUPABASE_ANON}', {{auth:{{flowType:'implicit'}}}});
const ALLOWED = ['{_ALLOWED_DOMAINS[0]}','{_ALLOWED_DOMAINS[1]}'];
_sb.auth.onAuthStateChange(async (event, session) => {{
  if (event === 'SIGNED_IN' && session) {{
    const email = session.user.email || '';
    if (!ALLOWED.some(d => email.endsWith(d))) {{
      await _sb.auth.signOut();
      document.getElementById('err').textContent = 'E-mail não autorizado.';
      return;
    }}
    document.cookie = 'sb_token=' + session.access_token + '; path=/; samesite=strict; max-age=3600';
    window.location.href = '/';
  }}
}});
document.getElementById('btn').addEventListener('click', async () => {{
  await _sb.auth.signInWithOAuth({{provider:'google',options:{{redirectTo:window.location.origin+'/'}}}});
}});
</script>
</body>
</html>"""


@app.route('/')
@app.route('/dashboard-crm.html')
def dashboard():
    if not _get_auth_email():
        return _LOGIN_HTML, 200, {'Content-Type': 'text/html; charset=utf-8'}
    path = os.path.join(_ROOT, 'dashboard-crm.html')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/auth/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('sb_token', '', expires=0, path='/')
    return resp


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
