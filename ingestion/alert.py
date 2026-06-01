"""Helper compartilhado: registra resultado de cron jobs em cron_logs."""
import logging
import os

logger = logging.getLogger(__name__)


def log_cron(job: str, status: str, message: str | None = None) -> None:
    """Grava resultado do cron (ok ou error) na tabela cron_logs."""
    try:
        from supabase import create_client
        sb = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )
        sb.table("cron_logs").insert({
            "job": job,
            "status": status,
            "message": message,
        }).execute()
    except Exception as e:
        logger.error({"event": "cron_log_failed", "error": str(e)})


def send_failure_alert(job: str, error: str) -> None:
    """Atalho para registrar falha — mantém compatibilidade com os crons."""
    log_cron(job, "error", error)
