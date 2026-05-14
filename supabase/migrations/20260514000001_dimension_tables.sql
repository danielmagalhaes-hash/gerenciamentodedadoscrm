-- Migration 001 — Tabelas de dimensão
-- Cria as "gavetas de referência" do banco: canais, ativos, formulários e dicionário de UTMs.
-- Esta migration também já popula os dados fixos que nunca mudam: os 5 canais e os 5 mapeamentos de UTM padrão.

-- Extensão para gerar IDs únicos (UUIDs)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- dim_channels — Os 5 canais do CRM
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_channels (
  id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  slug       text        NOT NULL UNIQUE,
  name       text        NOT NULL,
  utm_source text,
  utm_medium text,
  kpi_label  text        NOT NULL DEFAULT 'Receita por Disparo',
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO dim_channels (slug, name, utm_source, utm_medium) VALUES
  ('email_flow',     'E-mail Fluxo',        'email',     'flow'),
  ('email_campaign', 'E-mail Campanha',      'email',     'campaign'),
  ('wpp_flow',       'WhatsApp Fluxo',       'whatsapp',  'flow'),
  ('wpp_campaign',   'WhatsApp Campanha',    'whatsapp',  'campaign'),
  ('wpp_community',  'WhatsApp Comunidade',  'community',  null)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- dim_assets — Ativos pai: fluxos e campanhas por canal
-- source_tool indica de qual plataforma este ativo vem
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_assets (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id  uuid        NOT NULL REFERENCES dim_channels(id),
  name        text        NOT NULL,
  type        text        NOT NULL CHECK (type IN ('flow', 'campaign')),
  source_tool text        NOT NULL CHECK (source_tool IN ('klaviyo', 'vekta', 'sendflow', 'manual')),
  external_id text,
  is_active   boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- dim_asset_items — Ativos filho: e-mails e templates de WA
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_asset_items (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id    uuid        NOT NULL REFERENCES dim_assets(id),
  name        text        NOT NULL,
  type        text        NOT NULL CHECK (type IN ('email', 'wpp_template')),
  external_id text,
  position    integer,
  is_active   boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- dim_forms — Formulários e popups de captação (Klaviyo)
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_forms (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text        NOT NULL,
  type        text        NOT NULL CHECK (type IN ('popup', 'form', 'embed')),
  external_id text,
  channel_id  uuid        REFERENCES dim_channels(id),
  is_active   boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- dim_utm_mappings — Dicionário de UTMs
-- Traduz utm_source + utm_medium + utm_campaign → canal + ativo
-- is_mapped = true  → classificado pelo Daniel (usado na atribuição)
-- is_mapped = false → detectado automaticamente, aguardando classificação (Fase 3)
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_utm_mappings (
  id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  utm_source   text        NOT NULL,
  utm_medium   text,
  utm_campaign text,
  channel_id   uuid        NOT NULL REFERENCES dim_channels(id),
  asset_id     uuid        REFERENCES dim_assets(id),
  is_mapped    boolean     NOT NULL DEFAULT false,
  created_at   timestamptz NOT NULL DEFAULT now(),
  mapped_at    timestamptz
);

-- Índice único: COALESCE garante que NULL seja tratado como string vazia para fins de unicidade.
-- Isso evita que (email, flow, null) e (email, flow, null) coexistam como dois registros distintos.
CREATE UNIQUE INDEX IF NOT EXISTS idx_utm_mappings_unique
  ON dim_utm_mappings (utm_source, COALESCE(utm_medium, ''), COALESCE(utm_campaign, ''));

-- Seed: 5 mapeamentos padrão, já classificados (is_mapped = true)
-- utm_campaign = null significa "qualquer campanha com esse source+medium pertence a este canal"
INSERT INTO dim_utm_mappings (utm_source, utm_medium, utm_campaign, channel_id, is_mapped, mapped_at)
SELECT
  v.utm_source,
  v.utm_medium,
  v.utm_campaign,
  dc.id,
  true,
  now()
FROM (VALUES
  ('email',     'flow',     null::text, 'email_flow'),
  ('email',     'campaign', null::text, 'email_campaign'),
  ('whatsapp',  'flow',     null::text, 'wpp_flow'),
  ('whatsapp',  'campaign', null::text, 'wpp_campaign'),
  ('community', null::text, null::text, 'wpp_community')
) AS v(utm_source, utm_medium, utm_campaign, channel_slug)
JOIN dim_channels dc ON dc.slug = v.channel_slug
ON CONFLICT DO NOTHING;
