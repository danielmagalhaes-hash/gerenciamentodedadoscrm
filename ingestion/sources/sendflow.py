"""Cliente Sendflow — busca releases, analytics e ações de disparo da comunidade."""

import logging
import os
import time
from datetime import date

import httpx

from ingestion.models.sendflow_models import (
    SendflowAction,
    SendflowAnalytics,
    SendflowGroup,
    SendflowRelease,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://sendflow.pro/sendapi"
_ACTIONS_THROTTLE_S = 11  # API exige ≥10s entre chamadas de listagem de ações
_MAX_PAGES = 10            # teto da API: 1000 ações por paginação (10 × 100)
_RETRY_DELAYS_S = [3, 7, 15]  # aguarda antes de cada retentativa (403/429/5xx)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {os.environ['SENDFLOW_API_KEY']}"}


def _get(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    """GET com retry automático em 403/429/5xx (erros transientes do Sendflow)."""
    transient = {403, 429, 500, 502, 503, 504}
    for attempt, delay in enumerate(_RETRY_DELAYS_S + [None]):
        resp = client.get(url, **kwargs)
        if resp.status_code not in transient or delay is None:
            resp.raise_for_status()
            return resp
        logger.warning({
            "event": "sendflow_retry",
            "url": url,
            "status": resp.status_code,
            "attempt": attempt + 1,
            "wait_s": delay,
        })
        time.sleep(delay)
    raise RuntimeError("unreachable")  # satisfaz type checker


def fetch_releases() -> list[SendflowRelease]:
    """Retorna todas as releases (campanhas de comunidade) da conta."""
    with httpx.Client(headers=_headers(), timeout=30) as client:
        resp = _get(client, f"{_BASE_URL}/releases")
        return [SendflowRelease.model_validate(r) for r in resp.json()]


def fetch_release_groups(release_id: str) -> list[SendflowGroup]:
    """Retorna grupos vinculados a uma release com contagem atual de membros."""
    with httpx.Client(headers=_headers(), timeout=30) as client:
        resp = _get(client, f"{_BASE_URL}/releases/{release_id}/groups")
        return [SendflowGroup.model_validate(g) for g in resp.json()]


def fetch_release_analytics(release_id: str) -> SendflowAnalytics:
    """Retorna analytics históricos (add/remove/clicks por data) de uma release."""
    with httpx.Client(headers=_headers(), timeout=30) as client:
        resp = _get(client, f"{_BASE_URL}/releases/{release_id}/analytics")
        return SendflowAnalytics.model_validate(resp.json())


def fetch_release_actions(
    release_id: str,
    since: date | None = None,
    until: date | None = None,
) -> list[SendflowAction]:
    """
    Retorna ações de disparo (sendMessages, processed=true) de uma release.

    A API /actions não aceita type/processed/limit como query params — esses campos
    existem apenas no body de resposta. Filtragem é feita client-side.
    Pagina respeitando o rate limit de 10s entre chamadas.
    """
    actions: list[SendflowAction] = []
    cursor: str | None = None

    with httpx.Client(headers=_headers(), timeout=30) as client:
        for page in range(_MAX_PAGES):
            if page > 0:
                time.sleep(_ACTIONS_THROTTLE_S)

            params: dict = {"releaseId": release_id}
            if cursor:
                params["cursor"] = cursor

            resp = _get(client, f"{_BASE_URL}/actions", params=params)
            data = resp.json()

            page_actions = data.get("actions", [])
            for item in page_actions:
                action = SendflowAction.model_validate(item)

                logger.debug({
                    "event": "sendflow_action_raw",
                    "release_id": release_id,
                    "action_id": action.id,
                    "type": action.type,
                    "processed": action.processed,
                    "success": action.success,
                    "action_date": action.created_at.date().isoformat(),
                })

                # Filtra somente disparos processados com sucesso
                if action.type != "sendMessages" or not action.processed:
                    continue

                action_date = action.created_at.date()
                if since and action_date < since:
                    continue
                if until and action_date > until:
                    continue
                actions.append(action)

            cursor = data.get("nextCursor")
            if not cursor:
                break

    logger.info({
        "event": "sendflow_actions_fetched",
        "release_id": release_id,
        "count": len(actions),
    })
    return actions
