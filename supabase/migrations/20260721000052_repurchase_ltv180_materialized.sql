-- Migration: converte o LTV180 em materialized view (performance)
-- Reversível: sim
--   (recriar vw_repurchase_ltv180 como view simples, versão da migration 048)
--
-- Contexto: vw_repurchase_ltv180 respondia em 1-2,5s com a role anon, mas às vezes
-- estourava o statement_timeout (borderline, inconsistente). Materializada por
-- segurança, recalculada uma vez por dia no cron junto com as outras.

DROP VIEW IF EXISTS vw_repurchase_ltv180;

CREATE MATERIALIZED VIEW mv_repurchase_ltv180 AS
WITH customer_ltv AS (
    SELECT
        d.email,
        fp.first_purchase_date,
        SUM(d.amount_brl) AS revenue_180d
    FROM mv_repurchase_deals_dedup d
    JOIN mv_repurchase_customer_first_purchase fp USING (email)
    WHERE d.closed_at >= fp.first_purchase_date
      AND d.closed_at <  fp.first_purchase_date + INTERVAL '180 days'
    GROUP BY d.email, fp.first_purchase_date
)
SELECT
    date_trunc('month', first_purchase_date)::date AS cohort_month,
    COUNT(*)                    AS clientes_na_cohort,
    ROUND(AVG(revenue_180d), 2) AS ltv_180_medio
FROM customer_ltv
WHERE first_purchase_date <= (CURRENT_DATE - INTERVAL '180 days')
GROUP BY 1
ORDER BY 1;

CREATE UNIQUE INDEX idx_rd_ltv180_pk ON mv_repurchase_ltv180 (cohort_month);

GRANT SELECT ON mv_repurchase_ltv180 TO anon;

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
    REFRESH MATERIALIZED VIEW mv_repurchase_ltv180;
END;
$$;

GRANT EXECUTE ON FUNCTION refresh_repurchase_materialized_views() TO service_role;
