-- Migration: fact_repurchase_deals — base única para métricas de recompra/churn/reativação
-- Reversível: sim
--   DROP TABLE IF EXISTS fact_repurchase_deals;
--
-- Contexto: fonte combinada Shopify + comercial (etapa_do_negocio), vinda do data lake
-- (moon-ventures-data-lake.prod_silver.silver_deals_minimal). Substitui, para fins de
-- recompra/churn/reativação, o uso de fact_order_history_items/legacy (só Shopify).
-- Carga em duas partes, distinguidas pela coluna `source`:
--   - 'bq_historico': backfill único (2021-03-18 a 2026-06-30), nunca mais tocado.
--   - 'sheets_diario': recarregado por completo a cada execução do cron diário
--     (truncate+insert só dessa fatia — a planilha "Base de Dados" não tem chave única
--     de negócio, então upsert incremental não se aplica).
-- `first_purchase_date_raw` é mantido só de referência: a Instrução de Coortes do projeto
-- já identificou essa coluna como inconsistente na fonte. A 1ª compra real de cada cliente
-- deve ser recalculada nas views (MIN(closed_at) por email), nunca lida direto daqui.

CREATE TABLE IF NOT EXISTS fact_repurchase_deals (
    id                     uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                  text        NOT NULL,
    closed_at              date        NOT NULL,
    amount_brl             numeric(12,2) NOT NULL,
    is_first_purchase      boolean     NOT NULL,
    deal_stage             text        NOT NULL CHECK (deal_stage IN ('Shipped', 'Negócio Fechado - Comercial')),
    first_purchase_date_raw date,
    source                 text        NOT NULL CHECK (source IN ('bq_historico', 'sheets_diario')),
    ingested_at            timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE fact_repurchase_deals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_select_repurchase_deals"
    ON fact_repurchase_deals FOR SELECT TO anon USING (true);

CREATE POLICY "service_role_all_repurchase_deals"
    ON fact_repurchase_deals FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_repurchase_deals_email     ON fact_repurchase_deals (email);
CREATE INDEX IF NOT EXISTS idx_repurchase_deals_closed_at ON fact_repurchase_deals (closed_at);
CREATE INDEX IF NOT EXISTS idx_repurchase_deals_source    ON fact_repurchase_deals (source);
