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


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {os.environ['SENDFLOW_API_KEY']}"}


def fetch_releases() -> list[SendflowRelease]:
    """Retorna todas as releases (campanhas de comunidade) da conta."""
    with httpx.Client(headers=_headers(), timeout=30) as client:
        resp = client.get(f"{_BASE_URL}/releases")
        resp.raise_for_status()
        return [SendflowRelease.model_validate(r) for r in resp.json()]


def fetch_release_groups(release_id: str) -> list[SendflowGroup]:
    """Retorna grupos vinculados a uma release com contagem atual de membros."""
    with httpx.Client(headers=_headers(), timeout=30) as client:
        resp = client.get(f"{_BASE_URL}/releases/{release_id}/groups")
        resp.raise_for_status()
        return [SendflowGroup.model_validate(g) for g in resp.json()]


def fetch_release_analytics(release_id: str) -> SendflowAnalytics:
    """Retorna analytics históricos (add/remove/clicks por data) de uma release."""
    with httpx.Client(headers=_headers(), timeout=30) as client:
        resp = client.get(f"{_BASE_URL}/releases/{release_id}/analytics")
        resp.raise_for_status()
        return SendflowAnalytics.model_validate(resp.json())


def fetch_release_actions(
    release_id: str,
    since: date | None = None,
    until: date | None = None,
) -> list[SendflowAction]:
    """
    Retorna ações de disparo (sendMessages, processed=true) de uma release.

    Pagina respeitando o rate limit de 10s entre chamadas.
    Filtra client-side por [since, until] quando informados.
    """
    actions: list[SendflowAction] = []
    cursor: str | None = None

    with httpx.Client(headers=_headers(), timeout=30) as client:
        for page in range(_MAX_PAGES):
            if page > 0:
                time.sleep(_ACTIONS_THROTTLE_S)

            params: dict = {
                "releaseId": release_id,
                "type": "sendMessages",
                "processed": "true",
                "limit": 100,
            }
            if cursor:
                params["cursor"] = cursor

            resp = client.get(f"{_BASE_URL}/actions", params=params)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("actions", []):
                action = SendflowAction.model_validate(item)
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
