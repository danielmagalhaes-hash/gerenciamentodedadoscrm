-- Migration: converte as views base de recompra em materialized views (performance)
-- Reversível: sim
--   (recriar vw_repurchase_deals_dedup / vw_repurchase_customer_first_purchase
--    como views simples, versão anterior a esta migration)
--
-- Contexto: vw_repurchase_deals_dedup fazia GROUP BY em ~470 mil linhas a cada
-- consulta (statement timeout em produção). Convertida para materialized view,
-- recalculada uma vez por dia no cron (depois de carregar a planilha diária),
-- não a cada leitura do painel.

DROP VIEW IF EXISTS vw_repurchase_cohort_matrix;
DROP VIEW IF EXISTS vw_repurchase_ltv180;
DROP VIEW IF EXISTS vw_repurchase_customer_first_purchase;
DROP VIEW IF EXISTS vw_repurchase_deals_dedup;

CREATE MATERIALIZED VIEW mv_repurchase_deals_dedup AS
SELECT
    email,
    closed_at,
    SUM(amount_brl)            AS amount_brl,
    bool_or(is_first_purchase) AS is_first_purchase
FROM fact_repurchase_deals
WHERE is_first_purchase IS NOT NULL
GROUP BY email, closed_at;

CREATE UNIQUE INDEX idx_rd_dedup_pk ON mv_repurchase_deals_dedup (email, closed_at);
CREATE INDEX idx_rd_dedup_email ON mv_repurchase_deals_dedup (email);
CREATE INDEX idx_rd_dedup_closed_at ON mv_repurchase_deals_dedup (closed_at);

GRANT SELECT ON mv_repurchase_deals_dedup TO anon;

CREATE MATERIALIZED VIEW mv_repurchase_customer_first_purchase AS
SELECT
    email,
    COALESCE(
        MIN(closed_at) FILTER (WHERE is_first_purchase),
        MIN(closed_at)
    ) AS first_purchase_date
FROM mv_repurchase_deals_dedup
GROUP BY email;

CREATE UNIQUE INDEX idx_rd_first_purchase_email ON mv_repurchase_customer_first_purchase (email);

GRANT SELECT ON mv_repurchase_customer_first_purchase TO anon;

CREATE OR REPLACE VIEW vw_repurchase_ltv180 AS
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

GRANT SELECT ON vw_repurchase_ltv180 TO anon;

CREATE OR REPLACE VIEW vw_repurchase_cohort_matrix AS
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

GRANT SELECT ON vw_repurchase_cohort_matrix TO anon;

-- Função chamada via RPC pelo cron diário (ingestion/analytics), depois de recarregar
-- fact_repurchase_deals — mantém o SQL raw só na migration, nunca no código Python (CLAUDE.md).
CREATE OR REPLACE FUNCTION refresh_repurchase_materialized_views()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_repurchase_deals_dedup;
    REFRESH MATERIALIZED VIEW mv_repurchase_customer_first_purchase;
END;
$$;

GRANT EXECUTE ON FUNCTION refresh_repurchase_materialized_views() TO service_role;
