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

# Códigos que indicam problema com a key em si → tenta a próxima imediatamente
_KEY_ERROR_CODES = {401, 403, 429}
# Códigos de erro de servidor → retry com backoff antes de trocar de key
_SERVER_ERROR_CODES = {500, 502, 503, 504}


def _api_keys() -> list[str]:
    """Retorna lista de API keys disponíveis (primária + fallback)."""
    keys = [os.environ["SENDFLOW_API_KEY"]]
    key2 = os.environ.get("SENDFLOW_API_KEY_2", "").strip()
    if key2:
        keys.append(key2)
    return keys


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _get_with_key_fallback(url: str, params: dict | None = None) -> httpx.Response:
    """
    GET com fallback automático entre as duas API keys.

    - 401/403/429: troca de key imediatamente (sem retry na key atual).
    - 5xx: retry com backoff na key atual; se esgotar, troca de key.
    - Outras falhas: lança imediatamente.
    """
    keys = _api_keys()
    last_exc: Exception | None = None

    for key_idx, api_key in enumerate(keys):
        has_next = key_idx + 1 < len(keys)
        with httpx.Client(headers=_headers(api_key), timeout=30) as client:
            for attempt, delay in enumerate(_RETRY_DELAYS_S + [None]):
                resp = client.get(url, params=params or {})

                if resp.status_code in _KEY_ERROR_CODES:
                    # Key rejeitada/limitada — troca imediatamente, sem retry
                    if has_next:
                        logger.warning({
                            "event": "sendflow_key_fallback",
                            "url": url,
                            "status": resp.status_code,
                            "key_index": key_idx,
                        })
                        last_exc = httpx.HTTPStatusError(
                            f"Key {key_idx} rejeitada ({resp.status_code})",
                            request=resp.request, response=resp,
                        )
                        break  # sai do loop de tentativas → próxima key
                    resp.raise_for_status()

                if resp.status_code in _SERVER_ERROR_CODES and delay is not None:
                    # Erro de servidor → espera e tenta de novo com a mesma key
                    logger.warning({
                        "event": "sendflow_retry",
                        "url": url,
                        "status": resp.status_code,
                        "key_index": key_idx,
                        "attempt": attempt + 1,
                        "wait_s": delay,
                    })
                    time.sleep(delay)
                    continue

                resp.raise_for_status()
                return resp  # sucesso

    if last_exc:
        raise last_exc
    raise RuntimeError(f"Todas as {len(keys)} API key(s) do Sendflow falharam para {url}")


def fetch_releases() -> list[SendflowRelease]:
    """Retorna todas as releases (campanhas de comunidade) da conta."""
    resp = _get_with_key_fallback(f"{_BASE_URL}/releases")
    return [SendflowRelease.model_validate(r) for r in resp.json()]


def fetch_release_groups(release_id: str) -> list[SendflowGroup]:
    """Retorna grupos vinculados a uma release com contagem atual de membros."""
    resp = _get_with_key_fallback(f"{_BASE_URL}/releases/{release_id}/groups")
    return [SendflowGroup.model_validate(g) for g in resp.json()]


def fetch_release_analytics(release_id: str) -> SendflowAnalytics:
    """Retorna analytics históricos (add/remove/clicks por data) de uma release."""
    resp = _get_with_key_fallback(f"{_BASE_URL}/releases/{release_id}/analytics")
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

    for page in range(_MAX_PAGES):
        if page > 0:
            time.sleep(_ACTIONS_THROTTLE_S)

        params: dict = {"releaseId": release_id}
        if cursor:
            params["cursor"] = cursor

        resp = _get_with_key_fallback(f"{_BASE_URL}/actions", params=params)
        data = resp.json()

        for item in data.get("actions", []):
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
