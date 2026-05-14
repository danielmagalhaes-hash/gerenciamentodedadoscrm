-- Migration 002 — Tabelas de fato
-- Cria as "gavetas de eventos": pedidos, sessões, disparos e metas.
-- Estas tabelas recebem dados novos a cada ingestão (upsert).

-- ============================================================
-- fact_orders — Pedidos pagos com atribuição de canal
-- Upsert key: order_id
-- data_source: 'bigquery' para pedidos antes de 23/04/2025,
--              'shopify'  para pedidos a partir de 23/04/2025
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_orders (
  id                    uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id              text        NOT NULL UNIQUE,
  order_date            date        NOT NULL,
  customer_email        text        NOT NULL,
  revenue_brl           numeric(12,2) NOT NULL CHECK (revenue_brl > 0),
  is_first_purchase     boolean     NOT NULL,
  attributed_channel_id uuid        REFERENCES dim_channels(id),
  attributed_asset_id   uuid        REFERENCES dim_assets(id),
  utm_source            text,
  utm_medium            text,
  utm_campaign          text,
  data_source           text        NOT NULL DEFAULT 'shopify'
                          CHECK (data_source IN ('shopify', 'bigquery')),
  ingested_at           timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- fact_sessions — Sessões, ATC e BCO por canal por dia
-- Upsert key: (date, channel_id)
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_sessions (
  id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  date           date        NOT NULL,
  channel_id     uuid        NOT NULL REFERENCES dim_channels(id),
  sessions       integer     NOT NULL DEFAULT 0,
  add_to_cart    integer     NOT NULL DEFAULT 0,
  begin_checkout integer     NOT NULL DEFAULT 0,
  ingested_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (date, channel_id),
  CHECK (sessions >= 0),
  CHECK (sessions >= add_to_cart),
  CHECK (add_to_cart >= begin_checkout),
  CHECK (begin_checkout >= 0)
);

-- ============================================================
-- fact_email_sends — Métricas de e-mail por item de ativo por dia
-- Upsert key: (date, asset_item_id)
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_email_sends (
  id              uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  date            date          NOT NULL,
  asset_item_id   uuid          NOT NULL REFERENCES dim_asset_items(id),
  sends           integer       NOT NULL DEFAULT 0,
  delivered       integer       NOT NULL DEFAULT 0,
  opens           integer       NOT NULL DEFAULT 0,
  clicks          integer       NOT NULL DEFAULT 0,
  revenue_brl     numeric(12,2) NOT NULL DEFAULT 0,
  unsubscribes    integer       NOT NULL DEFAULT 0,
  bounces         integer       NOT NULL DEFAULT 0,
  spam_complaints integer       NOT NULL DEFAULT 0,
  ingested_at     timestamptz   NOT NULL DEFAULT now(),
  UNIQUE (date, asset_item_id)
);

-- ============================================================
-- fact_wpp_sends — Métricas de WhatsApp por template por dia
-- Upsert key: (date, asset_item_id)
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_wpp_sends (
  id            uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  date          date          NOT NULL,
  asset_item_id uuid          NOT NULL REFERENCES dim_asset_items(id),
  sends         integer       NOT NULL DEFAULT 0,
  delivered     integer       NOT NULL DEFAULT 0,
  read_count    integer       NOT NULL DEFAULT 0,
  replies       integer       NOT NULL DEFAULT 0,
  revenue_brl   numeric(12,2) NOT NULL DEFAULT 0,
  ingested_at   timestamptz   NOT NULL DEFAULT now(),
  UNIQUE (date, asset_item_id)
);

-- ============================================================
-- fact_wpp_subscribers — Inscritos por fluxo de WhatsApp por dia
-- Snapshot diário — apenas ativos do tipo 'flow' no canal wpp_flow.
-- A constraint R6 é verificada por trigger na migration 003.
-- Upsert key: (date, asset_id)
-- source_tool: 'hubspot' (temporário) ou 'klaviyo' (futuro)
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_wpp_subscribers (
  id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  date              date        NOT NULL,
  asset_id          uuid        NOT NULL REFERENCES dim_assets(id),
  subscribers_count integer     NOT NULL DEFAULT 0,
  source_tool       text        NOT NULL CHECK (source_tool IN ('hubspot', 'klaviyo')),
  ingested_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (date, asset_id)
);

-- ============================================================
-- fact_community_members — Snapshot diário de participantes da Comunidade
-- Upsert key: date
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_community_members (
  id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  date           date        NOT NULL UNIQUE,
  members_count  integer     NOT NULL DEFAULT 0,
  ingested_at    timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- fact_community_sends — Disparos de mensagens da Comunidade
-- Upsert key: external_id (ID do disparo na plataforma Sendflow)
-- Cada registro é um disparo individual, não um agregado diário.
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_community_sends (
  id               uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id      text          NOT NULL UNIQUE,
  sent_at          timestamptz   NOT NULL,
  content_type     text          CHECK (content_type IN ('text', 'image', 'video', 'audio', 'document')),
  recipients_count integer       NOT NULL DEFAULT 0,
  delivered        integer       NOT NULL DEFAULT 0,
  read_count       integer       NOT NULL DEFAULT 0,
  replies          integer       NOT NULL DEFAULT 0,
  revenue_brl      numeric(12,2) NOT NULL DEFAULT 0,
  ingested_at      timestamptz   NOT NULL DEFAULT now()
);

-- ============================================================
-- fact_lead_captures — Performance de formulários e popups por dia
-- Upsert key: (date, form_id)
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_lead_captures (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  date        date        NOT NULL,
  form_id     uuid        NOT NULL REFERENCES dim_forms(id),
  impressions integer     NOT NULL DEFAULT 0,
  submissions integer     NOT NULL DEFAULT 0,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (date, form_id)
);

-- ============================================================
-- fact_email_health — Saúde da base de e-mail por canal por dia
-- Upsert key: (date, channel_id)
-- active_subscribers = engajados nos últimos 90 dias
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_email_health (
  id                   uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  date                 date        NOT NULL,
  channel_id           uuid        NOT NULL REFERENCES dim_channels(id),
  list_size            integer     NOT NULL DEFAULT 0,
  active_subscribers   integer     NOT NULL DEFAULT 0,
  bounced_total        integer     NOT NULL DEFAULT 0,
  unsubscribed_total   integer     NOT NULL DEFAULT 0,
  ingested_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (date, channel_id)
);

-- ============================================================
-- fact_monthly_goals — Metas mensais de receita
-- Upsert key: month (sempre o primeiro dia do mês)
-- A soma dos componentes deve bater com o total (constraint R7).
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_monthly_goals (
  id                      uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  month                   date          NOT NULL UNIQUE,
  goal_total_brl          numeric(12,2) NOT NULL,
  goal_first_purchase_brl numeric(12,2) NOT NULL,
  goal_repurchase_brl     numeric(12,2) NOT NULL,
  created_at              timestamptz   NOT NULL DEFAULT now(),
  CHECK (goal_total_brl = goal_first_purchase_brl + goal_repurchase_brl)
);
