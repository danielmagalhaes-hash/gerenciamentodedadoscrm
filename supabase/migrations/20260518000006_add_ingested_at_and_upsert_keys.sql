-- Migration 006 — Colunas de rastreamento e chaves de upsert nas tabelas de dimensão
-- Reversível: sim (DROP COLUMN e DROP CONSTRAINT para desfazer)
--
-- Motivação: os scripts de ingestão Python fazem upsert nas tabelas dim_*
-- e precisam de:
--   1. ingested_at / updated_at para rastrear frescor dos dados (R12)
--   2. UNIQUE constraints para que o upsert ON CONFLICT funcione sem duplicatas

-- ============================================================
-- dim_assets
-- ============================================================
ALTER TABLE dim_assets
  ADD COLUMN IF NOT EXISTS updated_at  timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS ingested_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE dim_assets
  ADD CONSTRAINT IF NOT EXISTS uq_dim_assets_external_source
  UNIQUE (external_id, source_tool);

-- ============================================================
-- dim_asset_items
-- ============================================================
ALTER TABLE dim_asset_items
  ADD COLUMN IF NOT EXISTS updated_at  timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS ingested_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE dim_asset_items
  ADD CONSTRAINT IF NOT EXISTS uq_dim_asset_items_external_type
  UNIQUE (external_id, type);

-- ============================================================
-- dim_forms
-- ============================================================
ALTER TABLE dim_forms
  ADD COLUMN IF NOT EXISTS ingested_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE dim_forms
  ADD CONSTRAINT IF NOT EXISTS uq_dim_forms_external_id
  UNIQUE (external_id);
