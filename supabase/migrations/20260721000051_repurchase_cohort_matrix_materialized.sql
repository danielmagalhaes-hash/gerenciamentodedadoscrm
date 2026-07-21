-- Migration: converte a matriz de coortes em materialized view (performance)
-- Reversível: sim
--   (recriar vw_repurchase_cohort_matrix como view simples, versão da migration 047)
--
-- Contexto: mesmo filtrando por offset_months, a role anon (statement_timeout mais
-- curto que service_role) estourava timeout consultando vw_repurchase_cohort_matrix —
-- o filtro só era aplicado depois do JOIN+GROUP BY pesado sobre ~284 mil clientes.
-- Materializada, recalculada uma vez por dia no cron junto com as outras.

DROP VIEW IF EXISTS vw_repurchase_cohort_matrix;

CREATE MATERIALIZED VIEW mv_repurchase_cohort_matrix AS
WITH cohort_size AS (
    SELECT
        date_trunc('month', first_purchase_date)::date AS cohort_month,
        COUNT(*) AS clientes_adquiridos
    FROM mv_repurchase_customer_first_purchase
    GROUP BY 1
),
recompras AS (
    SELECT
        date_trunc('month', fp.first_purchase_date)::date AS cohort_month,
        (
            (EXTRACT(YEAR FROM d.closed_at)::int - EXTRACT(YEAR FROM fp.first_purchase_date)::int) * 12
            + (EXTRACT(MONTH FROM d.closed_at)::int - EXTRACT(MONTH FROM fp.first_purchase_date)::int)
        ) AS offset_months
    FROM mv_repurchase_deals_dedup d
    JOIN mv_repurchase_customer_first_purchase fp USING (email)
    WHERE d.is_first_purchase = false
)
SELECT
    cs.cohort_month,
    cs.clientes_adquiridos,
    r.offset_months,
    COUNT(*) AS transacoes_recompra
FROM cohort_size cs
JOIN recompras r ON r.cohort_month = cs.cohort_month
GROUP BY cs.cohort_month, cs.clientes_adquiridos, r.offset_months
ORDER BY cs.cohort_month, r.offset_months;

CREATE UNIQUE INDEX idx_rd_cohort_matrix_pk ON mv_repurchase_cohort_matrix (cohort_month, offset_months);

GRANT SELECT ON mv_repurchase_cohort_matrix TO anon;

CREATE OR REPLACE FUNCTION refresh_repurchase_materialized_views()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout = '5min'
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_repurchase_deals_dedup;
    REFRESH MATERIALIZED VIEW mv_repurchase_customer_first_purchase;
    REFRESH MATERIALIZED VIEW mv_repurchase_cohort_matrix;
END;
$$;

GRANT EXECUTE ON FUNCTION refresh_repurchase_materialized_views() TO service_role;
