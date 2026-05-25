"""Servidor HTTP leve para disparar ingestão sob demanda.

Roda em background thread junto ao scheduler.
Expõe:
  POST /sync?token=TOKEN  → inicia ingestão inteligente
  GET  /health            → healthcheck do Railway
  OPTIONS /*              → preflight CORS para o dashboard na Vercel
"""
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

MIN_SYNC_INTERVAL_SECS = 600  # 10 minutos entre syncs consecutivos

_last_sync_time: float = 0
_sync_lock = threading.Lock()
_sync_running = False
_sync_callback = None  # definido por start_sync_server()


def _execute_sync() -> None:
    global _sync_running
    try:
        if _sync_callback:
            _sync_callback()
    except Exception as e:
        logger.error({"event": "sync_failed", "error": str(e)})
    finally:
        _sync_running = False


def _request_sync() -> dict:
    global _last_sync_time, _sync_running

    with _sync_lock:
        now = time.time()
        secs_since_last = now - _last_sync_time
        if secs_since_last < MIN_SYNC_INTERVAL_SECS:
            wait = int(MIN_SYNC_INTERVAL_SECS - secs_since_last)
            return {"status": "rate_limited", "retry_in_seconds": wait,
                    "message": f"Aguarde {wait}s antes de sincronizar novamente."}
        if _sync_running:
            return {"status": "already_running",
                    "message": "Ingestão já está em andamento."}
        _last_sync_time = now
        _sync_running = True

    thread = threading.Thread(target=_execute_sync, daemon=True)
    thread.start()
    return {"status": "sync_started",
            "message": "Ingestão iniciada. Os dados aparecerão no dashboard em ~2 minutos."}


class _SyncHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # silencia logs padrão do http.server
        logger.debug(fmt, *args)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "sync_running": _sync_running})
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/sync":
            self._json(404, {"error": "not_found"})
            return

        token = parse_qs(parsed.query).get("token", [None])[0]
        expected = os.environ.get("SYNC_SECRET_TOKEN", "")

        if not expected:
            logger.error("SYNC_SECRET_TOKEN não configurado — endpoint de sync desativado")
            self._json(503, {"error": "sync_not_configured"})
            return
        if token != expected:
            self._json(401, {"error": "unauthorized"})
            return

        result = _request_sync()
        self._json(200, result)

    def _json(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def start_sync_server(sync_callback) -> None:
    """Inicia o servidor HTTP em background. sync_callback() é chamado ao receber POST /sync."""
    global _sync_callback
    _sync_callback = sync_callback

    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), _SyncHandler)
    logger.info({"event": "sync_server_started", "port": port})

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
