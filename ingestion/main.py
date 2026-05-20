import argparse
import logging
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

from ingestion.db.client import get_supabase_client
from ingestion.db import writers
from ingestion.sources import klaviyo as klaviyo_source
from ingestion.sources import google_sheets as sheets_source
from ingestion.sources import shopify as shopify_source

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

SHOPIFY_DAYS_LOOKBACK = 60
METRICS_WINDOW_DAYS = 7  # após 7 dias do envio, métricas de um e-mail não mudam


def run_klaviyo_ingestion(klaviyo_days: int | None = None) -> None:
    logger.info("=== Klaviyo: início da ingestão ===")
    today = date.today()

    sb = get_supabase_client()
    client = klaviyo_source.make_client()
    channel_ids = writers.get_channel_ids(sb)

    # 1. Sincroniza fluxos → dim_assets
    flows = klaviyo_source.fetch_flows(client)
    writers.upsert_flow_assets(sb, flows, channel_ids)

    # 2. Sincroniza campanhas → dim_assets
    campaigns = klaviyo_source.fetch_campaigns(client)
    writers.upsert_campaign_assets(sb, campaigns, channel_ids)

    # 3. Atualiza mapa de ativos após upsert
    asset_map = writers.get_asset_map(sb)

    # 4. Sincroniza e-mails de fluxos → dim_asset_items
    flow_messages = []
    for flow in flows:
        flow_messages.extend(klaviyo_source.fetch_flow_messages(client, flow.id))
    writers.upsert_flow_asset_items(sb, flow_messages, asset_map)

    # 5. Sincroniza mensagens de campanhas → dim_asset_items
    # Campanhas enviadas são imutáveis: pula as que já têm mensagens no banco
    synced_campaign_ids = writers.get_synced_campaign_ids(sb)
    new_campaigns = [c for c in campaigns if c.id not in synced_campaign_ids]
    logger.info({
        "event": "campaigns_to_sync",
        "total": len(campaigns),
        "new": len(new_campaigns),
        "already_synced": len(synced_campaign_ids),
    })
    campaign_messages = []
    for campaign in new_campaigns:
        campaign_messages.extend(klaviyo_source.fetch_campaign_messages(client, campaign.id))
    writers.upsert_campaign_asset_items(sb, campaign_messages, asset_map)

    # 6. Sincroniza métricas de e-mail → fact_email_sends
    # Regra: métricas são válidas apenas durante os 7 dias após o envio.
    # "since" = data de envio mais antiga entre campanhas ainda na janela ativa.
    # Para backfill (ex: puxar fevereiro pela primeira vez), passar --klaviyo-days N.
    if klaviyo_days is not None:
        metrics_since = today - timedelta(days=klaviyo_days)
        logger.info({"event": "metrics_backfill_forced", "since": metrics_since.isoformat()})
    else:
        active_campaigns = [
            c for c in campaigns
            if c.send_time and (c.send_time.date() + timedelta(days=METRICS_WINDOW_DAYS)) >= today
        ]
        metrics_since = min(
            (c.send_time.date() for c in active_campaigns),
            default=today - timedelta(days=METRICS_WINDOW_DAYS),
        )
        logger.info({"event": "metrics_since_auto", "since": metrics_since.isoformat(), "active_campaigns": len(active_campaigns)})

    item_map = writers.get_asset_item_map(sb)
    metric_rows = klaviyo_source.fetch_email_metrics_since(client, metrics_since)
    writers.upsert_email_sends(sb, metric_rows, item_map)

    # 7. Sincroniza formulários → dim_forms
    forms = klaviyo_source.fetch_forms(client)
    writers.upsert_forms(sb, forms)

    # 8. Sincroniza saúde da base → fact_email_health
    active_count = klaviyo_source.fetch_active_base_count(client)
    writers.upsert_email_health(sb, active_count, date.today(), channel_ids)

    logger.info("=== Klaviyo: ingestão finalizada ===")


def run_shopify_ingestion() -> None:
    logger.info("=== Shopify: início da ingestão ===")
    since = date.today() - timedelta(days=SHOPIFY_DAYS_LOOKBACK)
    sb = get_supabase_client()
    channel_ids = writers.get_channel_ids(sb)
    orders = shopify_source.fetch_paid_orders_since(since)
    writers.upsert_orders(sb, orders, channel_ids)
    logger.info("=== Shopify: ingestão finalizada ===")


def run_sheets_ingestion() -> None:
    logger.info("=== Google Sheets: início da ingestão ===")
    sb = get_supabase_client()
    channel_ids = writers.get_channel_ids(sb)
    session_rows, utm_rows = sheets_source.fetch_sessions_and_utm()
    writers.upsert_sessions(sb, session_rows, channel_ids)
    writers.upsert_sessions_utm(sb, utm_rows, channel_ids)
    logger.info("=== Google Sheets: ingestão finalizada ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="Roda a ingestão de dados do CRM")
    parser.add_argument(
        "--klaviyo-days", type=int, default=None,
        help=(
            "Força backfill de métricas a partir de N dias atrás. "
            "Padrão: automático — apenas campanhas dentro da janela de 7 dias após o envio."
        ),
    )
    args = parser.parse_args()

    sources = [
        ("klaviyo", lambda: run_klaviyo_ingestion(args.klaviyo_days)),
        ("shopify", run_shopify_ingestion),
        ("sheets", run_sheets_ingestion),
    ]
    for name, fn in sources:
        try:
            fn()
        except Exception as e:
            logger.error({"event": f"{name}_ingestion_failed", "error": str(e)})
            raise


if __name__ == "__main__":
    main()
