-- Migration: fact_repurchase_monthly_metrics — série mensal das métricas de recompra
-- Reversível: sim
--   DROP TABLE IF EXISTS fact_repurchase_monthly_metrics;
--
-- Contexto: calculado em Python (ingestion/analytics/repurchase_monthly_metrics.py),
-- extensão do script já validado em 2026-07-13 (modelo_recompra_taxas.py — mesma
-- lógica de ativos/churn/reentrantes, com o bug de rollforward já corrigido).
-- Recarregado por completo a cada execução do cron diário (truncate + insert):
-- a série inteira é recalculada do zero a partir de fact_repurchase_deals, então
-- não há necessidade de upsert incremental.
-- Nomenclatura confirmada com Daniel em 2026-07-21 (ignora termos da sessão anterior):
--   clientes_ativos       = clientes que compraram nos últimos 12 meses − recentes
--   taxa_repeticao         = recompra de clientes_ativos ÷ clientes_ativos
--   taxa_reativacao        = compras de clientes que estavam inativos ÷ clientes_inativos
--   clientes_inativos      = clientes com mais de 12 meses sem comprar (contagem no fim do mês)
--   clientes_em_risco_m11_m12 = clientes cujo tempo desde a última compra está em 11 ou 12 meses

CREATE TABLE IF NOT EXISTS fact_repurchase_monthly_metrics (
    month                      date        PRIMARY KEY,
    clientes_ativos            integer     NOT NULL,
    clientes_recentes          integer     NOT NULL,
    clientes_inativos          integer     NOT NULL,
    clientes_em_risco_m11_m12  integer     NOT NULL,
    clientes_novos             integer     NOT NULL,
    clientes_reentrantes       integer     NOT NULL,
    clientes_churn             integer     NOT NULL,
    taxa_churn                 numeric(7,4),
    taxa_repeticao             numeric(7,4),
    compras_de_inativos        integer     NOT NULL,
    taxa_reativacao            numeric(7,4),
    ingested_at                timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE fact_repurchase_monthly_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_select_repurchase_monthly_metrics"
    ON fact_repurchase_monthly_metrics FOR SELECT TO anon USING (true);

CREATE POLICY "service_role_all_repurchase_monthly_metrics"
    ON fact_repurchase_monthly_metrics FOR ALL TO service_role USING (true) WITH CHECK (true);
