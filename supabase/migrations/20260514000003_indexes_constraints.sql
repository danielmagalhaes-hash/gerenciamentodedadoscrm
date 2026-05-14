-- Migration 003 — Índices de performance e constraints adicionais
-- Cria os "atalhos de busca" que tornam as consultas rápidas,
-- e a regra R6 que impede inscritos de WhatsApp em ativos errados.

-- ============================================================
-- Índices em fact_orders
-- As consultas mais comuns filtram por data e canal.
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_orders_date
  ON fact_orders (order_date);

CREATE INDEX IF NOT EXISTS idx_fact_orders_channel
  ON fact_orders (attributed_channel_id);

CREATE INDEX IF NOT EXISTS idx_fact_orders_date_channel
  ON fact_orders (order_date, attributed_channel_id);

CREATE INDEX IF NOT EXISTS idx_fact_orders_customer
  ON fact_orders (customer_email);

CREATE INDEX IF NOT EXISTS idx_fact_orders_data_source
  ON fact_orders (data_source);

-- ============================================================
-- Índices em fact_sessions
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_sessions_date
  ON fact_sessions (date);

CREATE INDEX IF NOT EXISTS idx_fact_sessions_channel
  ON fact_sessions (channel_id);

-- ============================================================
-- Índices em fact_email_sends
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_email_sends_date
  ON fact_email_sends (date);

CREATE INDEX IF NOT EXISTS idx_fact_email_sends_item
  ON fact_email_sends (asset_item_id);

-- ============================================================
-- Índices em fact_wpp_sends
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_wpp_sends_date
  ON fact_wpp_sends (date);

CREATE INDEX IF NOT EXISTS idx_fact_wpp_sends_item
  ON fact_wpp_sends (asset_item_id);

-- ============================================================
-- Índices em fact_wpp_subscribers
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_wpp_subscribers_asset
  ON fact_wpp_subscribers (asset_id);

CREATE INDEX IF NOT EXISTS idx_fact_wpp_subscribers_date
  ON fact_wpp_subscribers (date);

-- ============================================================
-- Índices em fact_community_sends
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_community_sends_sent_at
  ON fact_community_sends (sent_at);

-- ============================================================
-- Índices em fact_lead_captures
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_lead_captures_date
  ON fact_lead_captures (date);

CREATE INDEX IF NOT EXISTS idx_fact_lead_captures_form
  ON fact_lead_captures (form_id);

-- ============================================================
-- Índices em fact_email_health
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fact_email_health_date
  ON fact_email_health (date);

CREATE INDEX IF NOT EXISTS idx_fact_email_health_channel
  ON fact_email_health (channel_id);

-- ============================================================
-- Índices em dim_assets
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_dim_assets_channel
  ON dim_assets (channel_id);

CREATE INDEX IF NOT EXISTS idx_dim_assets_type
  ON dim_assets (type);

-- ============================================================
-- Índices em dim_asset_items
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_dim_asset_items_asset
  ON dim_asset_items (asset_id);

CREATE INDEX IF NOT EXISTS idx_dim_asset_items_type
  ON dim_asset_items (type);

-- ============================================================
-- Índices em dim_utm_mappings
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_utm_mappings_channel
  ON dim_utm_mappings (channel_id);

CREATE INDEX IF NOT EXISTS idx_utm_mappings_is_mapped
  ON dim_utm_mappings (is_mapped);

-- ============================================================
-- Regra R6 — Trigger em fact_wpp_subscribers
-- Garante que inscritos de WhatsApp só possam ser gravados
-- para ativos do tipo 'flow' pertencentes ao canal wpp_flow.
-- Campanhas de WhatsApp não têm inscritos.
-- ============================================================
CREATE OR REPLACE FUNCTION fn_check_wpp_subscriber_asset()
RETURNS trigger AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM dim_assets   da
    JOIN dim_channels dc ON dc.id = da.channel_id
    WHERE da.id   = NEW.asset_id
      AND da.type = 'flow'
      AND dc.slug = 'wpp_flow'
  ) THEN
    RAISE EXCEPTION
      'fact_wpp_subscribers: asset_id % não é um fluxo do canal wpp_flow.',
      NEW.asset_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_wpp_subscriber_asset
  BEFORE INSERT OR UPDATE ON fact_wpp_subscribers
  FOR EACH ROW EXECUTE FUNCTION fn_check_wpp_subscriber_asset();
