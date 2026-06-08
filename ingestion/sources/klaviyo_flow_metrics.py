import os
import time
import logging
from datetime import date, timedelta

import httpx
from supabase import Client

from ingestion.db.writers import get_flow_message_structure
from ingestion.models.klaviyo_models import KlaviyoFlowEmailMetric

logger = logging.getLogger(__name__)

BASE_URL = "https://a.klaviyo.com/api"
REVISION = "2024-10-15"
MAX_RETRIES = 6
GET_THROTTLE_SECS = 0.2
METRIC_THROTTLE_SECS = 0.3  # 3.3 req/s — dentro do limite de 5 req/s da Klaviyo

# Coluna do banco -> nome do evento no Klaviyo
FLOW_METRIC_MAP: dict[str, str] = {
    "email_enviado": "Received Email",
    "email_aberto":  "Opened Email",
    "email_clicado": "Clicked Email",
}


def make_client() -> httpx.Client:
    key = os.environ["KLAVIYO_PRIVATE_API_KEY"]
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Klaviyo-API-Key {key}", "revision": REVISION},
        timeout=60.0,
    )


def _get(client: httpx.Client, path: str, params: dict | None = None) -> dict:
    time.sleep(GET_THROTTLE_SECS)
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(path, params=params)
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            wait = 2 ** (attempt + 1)
            logger.warning({"event": "timeout_retry", "path": path, "wait_secs": wait})
            time.sleep(wait)
            continue
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 2 ** (attempt + 1)))
            logger.warning({"event": "rate_limit", "path": path, "wait_secs": retry_after})
            time.sleep(retry_after)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Max retries exceeded: GET {path}")


def _post_aggregate(client: httpx.Client, body: dict) -> dict:
    time.sleep(METRIC_THROTTLE_SECS)
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.post("/metric-aggregates/", json=body)
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            wait = 2 ** (attempt + 1)
            logger.warning({"event": "timeout_retry_post", "wait_secs": wait})
            time.sleep(wait)
            continue
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 2 ** attempt))
            logger.warning({"event": "rate_limit_post", "wait_secs": wait})
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError("Max retries exceeded: POST /metric-aggregates/")


def _paginate(client: httpx.Client, path: str, params: dict) -> list[dict]:
    result: list[dict] = []
    body = _get(client, path, params)
    result.extend(body.get("data", []))
    next_url = (body.get("links") or {}).get("next")
    while next_url:
        body = _get(client, next_url)
        result.extend(body.get("data", []))
        next_url = (body.get("links") or {}).get("next")
    return result


def _fetch_metric_ids(client: httpx.Client) -> dict[str, str]:
    target_names = set(FLOW_METRIC_MAP.values())
    mapping: dict[str, str] = {}
    for item in _paginate(client, "/metrics/", {"fields[metric]": "name"}):
        name = item["attributes"].get("name", "")
        if name in target_names:
            mapping[name] = item["id"]
    missing = target_names - set(mapping.keys())
    if missing:
        logger.warning({"event": "metrics_not_found", "missing": list(missing)})
    return mapping


def _aggregate_for_flow(
    client: httpx.Client,
    metric_id: str,
    flow_id: str,
    date_from: date,
    date_to: date,
) -> dict[str, dict[str, int]]:
    """Retorna {message_id: {date_iso: count}} para uma métrica de um fluxo inteiro.

    Usa by=['$message'] para receber o breakdown por e-mail numa única chamada
    por fluxo×métrica — reduz de ~1.530 para ~93 chamadas por execução.
    """
    body = {"data": {"type": "metric-aggregate", "attributes": {
        "metric_id": metric_id,
        "measurements": ["count"],
        "interval": "day",
        "by": ["$message"],
        "page_size": 500,
        "filter": (
            f"and("
            f"greater-or-equal(datetime,{date_from.isoformat()}T00:00:00+00:00),"
            f"less-than(datetime,{(date_to + timedelta(days=1)).isoformat()}T00:00:00+00:00),"
            f"equals($flow,\"{flow_id}\")"
            f")"
        ),
    }}}
    resp = _post_aggregate(client, body)
    attrs = resp["data"]["attributes"]
    raw_dates: list[str] = attrs.get("dates", [])
    date_strs = [d[:10] for d in raw_dates]

    result: dict[str, dict[str, int]] = {}
    for row in attrs.get("data", []):
        dimensions = row.get("dimensions", [])
        if not dimensions:
            continue
        message_id = dimensions[0]
        counts: dict[str, int] = {}
        for i, count in enumerate(row["measurements"].get("count", [])):
            if count and i < len(date_strs):
                counts[date_strs[i]] = int(count)
        if counts:
            result[message_id] = counts
    return result


def fetch_flow_email_metrics(
    client: httpx.Client,
    sb: Client,
    date_from: date,
    date_to: date,
) -> list[KlaviyoFlowEmailMetric]:
    """Busca métricas diárias de e-mails de todos os fluxos ativos.

    Lê estrutura de dim_assets + dim_asset_items (zero chamadas GET ao Klaviyo).
    Para cada fluxo × 3 métricas faz uma única chamada POST com by=['$message'],
    recebendo o breakdown por e-mail de uma vez — ~93 chamadas no total.
    """
    all_messages = get_flow_message_structure(sb)
    if not all_messages:
        logger.warning({
            "event": "no_flow_messages_in_db",
            "hint": "execute o cron email_structure antes de email_flow",
        })
        return []

    # Agrupa mensagens por flow_id
    flows_map: dict[str, list[dict]] = {}
    for msg in all_messages:
        flows_map.setdefault(msg["flow_id"], []).append(msg)

    logger.info({
        "event": "flow_metrics_start",
        "flows": len(flows_map),
        "messages": len(all_messages),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    })

    metric_ids = _fetch_metric_ids(client)
    rows: dict[tuple[str, str], dict] = {}

    for flow_id, messages in flows_map.items():
        flow_name = messages[0]["flow_name"]
        msg_lookup = {m["message_id"]: m for m in messages}

        for col_name, metric_name in FLOW_METRIC_MAP.items():
            metric_id = metric_ids.get(metric_name)
            if not metric_id:
                continue

            counts_by_message = _aggregate_for_flow(
                client, metric_id, flow_id, date_from, date_to
            )

            for message_id, msg_counts in counts_by_message.items():
                msg = msg_lookup.get(message_id)
                if not msg:
                    continue
                for date_str, count in msg_counts.items():
                    if count == 0:
                        continue
                    key = (message_id, date_str)
                    if key not in rows:
                        rows[key] = {
                            "flow_id":       flow_id,
                            "flow_name":     flow_name,
                            "message_id":    message_id,
                            "message_name":  msg["message_name"],
                            "data":          date.fromisoformat(date_str),
                            "email_enviado": 0,
                            "email_aberto":  0,
                            "email_clicado": 0,
                        }
                    rows[key][col_name] = count

        logger.info({
            "event": "flow_processed",
            "flow_name": flow_name,
            "messages": len(messages),
        })

    result = [KlaviyoFlowEmailMetric.model_validate(r) for r in rows.values()]
    logger.info({"event": "flow_metrics_done", "rows": len(result)})
    return result
