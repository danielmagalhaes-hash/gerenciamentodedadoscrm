import logging
from datetime import date, datetime, timezone

from supabase import Client

from ingestion.models.klaviyo_models import (
    KlaviyoCampaign,
    KlaviyoCampaignMessage,
    KlaviyoEmailMetricRow,
    KlaviyoFlow,
    KlaviyoFlowMessage,
    KlaviyoForm,
)

logger = logging.getLogger(__name__)

ACTIVE_CAMPAIGN_STATUSES = {"Sent", "Sending", "Scheduled"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_channel_ids(sb: Client) -> dict[str, str]:
    """Retorna {slug: uuid} de todos os canais em dim_channels."""
    resp = sb.table("dim_channels").select("id,slug").execute()
    return {row["slug"]: row["id"] for row in resp.data}


def get_asset_map(sb: Client) -> dict[str, str]:
    """Retorna {external_id: uuid} de todos os ativos Klaviyo em dim_assets."""
    resp = (
        sb.table("dim_assets")
        .select("id,external_id")
        .eq("source_tool", "klaviyo")
        .execute()
    )
    return {row["external_id"]: row["id"] for row in resp.data}


def get_asset_item_map(sb: Client) -> dict[str, str]:
    """Retorna {external_id: uuid} de todos os itens de e-mail em dim_asset_items."""
    resp = (
        sb.table("dim_asset_items")
        .select("id,external_id")
        .eq("type", "email")
        .execute()
    )
    return {row["external_id"]: row["id"] for row in resp.data}


def upsert_flow_assets(sb: Client, flows: list[KlaviyoFlow], channel_ids: dict[str, str]) -> int:
    if not flows:
        return 0
    now = _now_iso()
    channel_id = channel_ids["email_flow"]
    records = [{
        "external_id": f.id,
        "channel_id": channel_id,
        "name": f.name,
        "type": "flow",
        "is_active": f.status == "live",
        "source_tool": "klaviyo",
        "updated_at": now,
        "ingested_at": now,
    } for f in flows]
    sb.table("dim_assets").upsert(records, on_conflict="external_id,source_tool").execute()
    logger.info({"event": "flow_assets_upserted", "count": len(records)})
    return len(records)


def upsert_campaign_assets(sb: Client, campaigns: list[KlaviyoCampaign], channel_ids: dict[str, str]) -> int:
    if not campaigns:
        return 0
    now = _now_iso()
    channel_id = channel_ids["email_campaign"]
    records = [{
        "external_id": c.id,
        "channel_id": channel_id,
        "name": c.name,
        "type": "campaign",
        "is_active": c.status in ACTIVE_CAMPAIGN_STATUSES,
        "source_tool": "klaviyo",
        "updated_at": now,
        "ingested_at": now,
    } for c in campaigns]
    sb.table("dim_assets").upsert(records, on_conflict="external_id,source_tool").execute()
    logger.info({"event": "campaign_assets_upserted", "count": len(records)})
    return len(records)


def upsert_flow_asset_items(
    sb: Client, messages: list[KlaviyoFlowMessage], asset_map: dict[str, str]
) -> int:
    if not messages:
        return 0
    now = _now_iso()
    records = []
    skipped = 0
    for m in messages:
        asset_id = asset_map.get(m.flow_id)
        if not asset_id:
            skipped += 1
            continue
        records.append({
            "external_id": m.id,
            "asset_id": asset_id,
            "name": m.name,
            "type": "email",
            "position": m.position,
            "updated_at": now,
            "ingested_at": now,
        })
    if skipped:
        logger.warning({"event": "flow_items_skipped", "skipped": skipped})
    if not records:
        return 0
    sb.table("dim_asset_items").upsert(records, on_conflict="external_id,type").execute()
    logger.info({"event": "flow_asset_items_upserted", "count": len(records)})
    return len(records)


def upsert_campaign_asset_items(
    sb: Client, messages: list[KlaviyoCampaignMessage], asset_map: dict[str, str]
) -> int:
    if not messages:
        return 0
    now = _now_iso()
    records = []
    skipped = 0
    for m in messages:
        asset_id = asset_map.get(m.campaign_id)
        if not asset_id:
            skipped += 1
            continue
        records.append({
            "external_id": m.id,
            "asset_id": asset_id,
            "name": m.label,
            "type": "email",
            "position": None,
            "updated_at": now,
            "ingested_at": now,
        })
    if skipped:
        logger.warning({"event": "campaign_items_skipped", "skipped": skipped})
    if not records:
        return 0
    sb.table("dim_asset_items").upsert(records, on_conflict="external_id,type").execute()
    logger.info({"event": "campaign_asset_items_upserted", "count": len(records)})
    return len(records)


def upsert_email_sends(
    sb: Client, rows: list[KlaviyoEmailMetricRow], item_map: dict[str, str]
) -> int:
    if not rows:
        return 0
    now = _now_iso()
    records = []
    skipped = 0
    for r in rows:
        item_id = item_map.get(r.message_id)
        if not item_id:
            skipped += 1
            continue
        records.append({
            "date": r.date.isoformat(),
            "asset_item_id": item_id,
            "sends": r.sends,
            "opens": r.opens,
            "clicks": r.clicks,
            "bounces": r.bounces,
            "spam_complaints": r.spam_complaints,
            "unsubscribes": r.unsubscribes,
            "ingested_at": now,
        })
    if skipped:
        logger.warning({"event": "email_sends_skipped", "skipped": skipped, "reason": "message_id not in dim_asset_items"})
    if not records:
        return 0
    sb.table("fact_email_sends").upsert(records, on_conflict="date,asset_item_id").execute()
    logger.info({"event": "email_sends_upserted", "count": len(records)})
    return len(records)


def upsert_forms(sb: Client, forms: list[KlaviyoForm]) -> int:
    if not forms:
        return 0
    now = _now_iso()
    records = [{
        "external_id": f.id,
        "name": f.name,
        "type": f.form_type,
        "is_active": f.status.lower() not in ("draft", "archived"),
        "ingested_at": now,
    } for f in forms]
    sb.table("dim_forms").upsert(records, on_conflict="external_id").execute()
    logger.info({"event": "forms_upserted", "count": len(records)})
    return len(records)


def upsert_email_health(
    sb: Client, active_base_count: int, today: date, channel_ids: dict[str, str]
) -> int:
    now = _now_iso()
    record = {
        "date": today.isoformat(),
        "channel_id": channel_ids["email_flow"],
        "active_base_count": active_base_count,
        "ingested_at": now,
    }
    sb.table("fact_email_health").upsert([record], on_conflict="date,channel_id").execute()
    logger.info({"event": "email_health_upserted", "active_base_count": active_base_count})
    return 1
