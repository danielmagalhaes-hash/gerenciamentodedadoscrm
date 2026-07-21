-- Migration: views de LTV180 e matriz de coortes para métricas de recompra
-- Reversível: sim
--   DROP VIEW IF EXISTS vw_repurchase_cohort_matrix;
--   DROP VIEW IF EXISTS vw_repurchase_ltv180;
--   DROP VIEW IF EXISTS vw_repurchase_customer_first_purchase;
--   DROP VIEW IF EXISTS vw_repurchase_deals_dedup;
--
-- Contexto: fact_repurchase_deals tem linhas por item/negócio — pedidos com vários
-- itens geram várias linhas com o mesmo (email, closed_at). Por instrução do Daniel
-- (2026-07-21), a análise sempre trata (email, closed_at) como o negócio único;
-- vw_repurchase_deals_dedup agrupa por esse par (soma o valor das linhas do mesmo
-- negócio, já que representam itens de uma mesma compra) e descarta linhas sem
-- classificação de tipo_de_venda (is_first_purchase nulo, ~17 linhas fora do escopo).
--
-- 1ª compra de cada cliente é recalculada (nunca lida de first_purchase_date_raw,
-- que a Instrução de Coortes do projeto já identificou como inconsistente na fonte):
-- MIN(closed_at) onde is_first_purchase=true; fallback MIN(closed_at) geral.
--
-- Estas views são "foto atual" (LTV180 por coorte, matriz M+0..M+n) — não recalculam
-- mês a mês quem está ativo/inativo; isso vive em fact_repurchase_monthly_metrics
-- (calculado em Python, ver ingestion/analytics/repurchase_monthly_metrics.py).

CREATE OR REPLACE VIEW vw_repurchase_deals_dedup AS
SELECT
    email,
    closed_at,
    SUM(amount_brl)      AS amount_brl,
    bool_or(is_first_purchase) AS is_first_purchase
FROM fact_repurchase_deals
WHERE is_first_purchase IS NOT NULL
GROUP BY email, closed_at;

GRANT SELECT ON vw_repurchase_deals_dedup TO anon;

CREATE OR REPLACE VIEW vw_repurchase_customer_first_purchase AS
SELECT
    email,
    COALESCE(
        MIN(closed_at) FILTER (WHERE is_first_purchase),
        MIN(closed_at)
    ) AS first_purchase_date
FROM vw_repurchase_deals_dedup
GROUP BY email;

GRANT SELECT ON vw_repurchase_customer_first_purchase TO anon;

-- LTV 180 dias: receita média por cliente nos 180 dias após a 1ª compra, agrupado
-- por mês de aquisição. Só inclui coortes onde os 180 dias já se completaram.
CREATE OR REPLACE VIEW vw_repurchase_ltv180 AS
WITH customer_ltv AS (
    SELECT
        d.email,
        fp.first_purchase_date,
        SUM(d.amount_brl) AS revenue_180d
    FROM vw_repurchase_deals_dedup d
    JOIN vw_repurchase_customer_first_purchase fp USING (email)
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

-- Matriz de coortes M+0..M+n em formato longo (cohort_month, offset_months, transacoes) —
-- o painel monta a matriz visual a partir disso. Célula = nº de transações de recompra
-- (is_first_purchase=false), igual à Instrução de Coortes do projeto.
CREATE OR REPLACE VIEW vw_repurchase_cohort_matrix AS
WITH cohort_size AS (
    SELECT
        date_trunc('month', first_purchase_date)::date AS cohort_month,
        COUNT(*) AS clientes_adquiridos
    FROM vw_repurchase_customer_first_purchase
    GROUP BY 1
),
recompras AS (
    SELECT
        date_trunc('month', fp.first_purchase_date)::date AS cohort_month,
        (
            (EXTRACT(YEAR FROM d.closed_at)::int - EXTRACT(YEAR FROM fp.first_purchase_date)::int) * 12
            + (EXTRACT(MONTH FROM d.closed_at)::int - EXTRACT(MONTH FROM fp.first_purchase_date)::int)
        ) AS offset_months
    FROM vw_repurchase_deals_dedup d
    JOIN vw_repurchase_customer_first_purchase fp USING (email)
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
