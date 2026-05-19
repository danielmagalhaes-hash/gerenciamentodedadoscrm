import csv
import io
import logging
import os
from datetime import date, datetime
from decimal import Decimal

import httpx

from ingestion.models.shopify_models import ShopifyOrder

logger = logging.getLogger(__name__)


def fetch_paid_orders_since(since: date) -> list[ShopifyOrder]:
    """Busca pedidos pagos via CSV do Google Sheets (export do app Shopify).

    Filtra is_last_before_purchase=TRUE para garantir atribuição last-click (R4).
    """
    url = os.environ["SHOPIFY_SHEETS_CSV_URL"]
    logger.info({"event": "shopify_fetch_start", "since": since.isoformat()})

    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()

    orders: list[ShopifyOrder] = []
    skipped_not_last = 0
    skipped_not_paid = 0
    skipped_old = 0

    reader = csv.DictReader(io.StringIO(resp.text))
    for row in reader:
        if row.get("is_last_before_purchase", "").strip().upper() != "TRUE":
            skipped_not_last += 1
            continue
        if row.get("financial_status", "").strip().upper() != "PAID":
            skipped_not_paid += 1
            continue

        try:
            order_date = datetime.strptime(row["processed_at_data"].strip(), "%d/%m/%Y").date()
        except ValueError:
            logger.warning({"event": "shopify_date_parse_failed", "value": row.get("processed_at_data")})
            continue

        if order_date < since:
            skipped_old += 1
            continue

        # Extrai ID numérico do GID: "gid://shopify/Order/6998503293180" → "6998503293180"
        raw_id = row["order_id"].strip()
        order_id = raw_id.split("/")[-1] if "/" in raw_id else raw_id

        # Formato BR: "1.376,56" → Decimal("1376.56")
        raw_revenue = row.get("net_revenue", "0").strip().replace(".", "").replace(",", ".")
        revenue = Decimal(raw_revenue) if raw_revenue else Decimal("0")

        if revenue <= 0:
            continue

        orders.append(ShopifyOrder(
            order_id=order_id,
            order_date=order_date,
            customer_email=row.get("customer_email", "").strip().lower(),
            revenue_brl=revenue,
            is_first_purchase=(row.get("customer_type", "").strip() == "Primeira Compra"),
            utm_source=row.get("utm_source", "").strip() or None,
            utm_medium=row.get("utm_medium", "").strip() or None,
            utm_campaign=row.get("utm_campaign", "").strip() or None,
        ))

    logger.info({
        "event": "shopify_orders_fetched",
        "count": len(orders),
        "skipped_not_last": skipped_not_last,
        "skipped_not_paid": skipped_not_paid,
        "skipped_old": skipped_old,
    })
    return orders
