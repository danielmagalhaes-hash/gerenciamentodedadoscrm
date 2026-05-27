-- Migration: adiciona utm_term em fact_orders + split de receita por audiência na view
-- Reversível: sim
--
-- utm_term distingue a audiência dentro de um mesmo utm_content (ex: em1249 tem Clientes, Leads, Base Total).
-- Os valores de utm_term têm muitas variantes não padronizadas, então normalizamos no subquery:
--   utm_term LIKE 'clientes%' → 'clientes'
--   utm_term LIKE 'leads%'    → 'leads'
--   utm_term = 'basetotal'    → 'basetotal'
--   demais                    → 'other'
-- Emails com tag [CLIENTES/LEADS/BASE] no nome usam o split por audiência.
-- Emails sem tag de audiência usam o total do utm_content como fallback.

ALTER TABLE fact_orders ADD COLUMN IF NOT EXISTS utm_term TEXT;
CREATE INDEX IF NOT EXISTS idx_fact_orders_utm_term ON fact_orders (utm_term) WHERE utm_term IS NOT NULL;

DROP VIEW IF EXISTS vw_email_asset_metrics;

CREATE VIEW vw_email_asset_metrics AS
SELECT
  da.id                                                                              AS asset_id,
  da.name                                                                            AS asset_name,
  da.type                                                                            AS asset_type,
  da.is_active,
  dc.slug                                                                            AS channel_slug,
  MIN(fes.date)                                                                      AS first_date,
  MAX(fes.date)                                                                      AS last_date,
  MIN(CASE WHEN fes.sends > 0 THEN fes.date END)                                    AS send_date,
  SUM(fes.sends)                                                                     AS sends,
  SUM(fes.opens)                                                                     AS opens,
  SUM(fes.clicks)                                                                    AS clicks,
  SUM(fes.bounces)                                                                   AS bounces,
  SUM(fes.unsubscribes)                                                              AS unsubscribes,
  ROUND(SUM(fes.opens)::numeric  / NULLIF(SUM(fes.sends), 0)::numeric * 100, 2)    AS open_rate_pct,
  ROUND(SUM(fes.clicks)::numeric / NULLIF(SUM(fes.opens), 0)::numeric * 100, 2)    AS ctor_pct,
  ROUND(SUM(fes.sends)::numeric  / NULLIF(COUNT(DISTINCT fes.date), 0)::numeric, 1) AS sends_per_day,
  LOWER((regexp_match(da.name, '\[([a-zA-Z0-9]+)\]'))[1])                           AS utm_content_code,
  COALESCE(MAX(fo_seg.revenue_brl), MAX(fo_tot.revenue_brl), 0)                    AS revenue_brl,
  ROUND(
    COALESCE(MAX(fo_seg.revenue_brl), MAX(fo_tot.revenue_brl), 0)
    / NULLIF(SUM(fes.sends), 0),
    4
  )                                                                                  AS revenue_per_send
FROM fact_email_sends fes
JOIN dim_asset_items  dai ON dai.id = fes.asset_item_id
JOIN dim_assets       da  ON da.id  = dai.asset_id
JOIN dim_channels     dc  ON dc.id  = da.channel_id
LEFT JOIN (
  SELECT
    LOWER(utm_content) AS utm_content,
    CASE
      WHEN LOWER(utm_term) LIKE 'clientes%' THEN 'clientes'
      WHEN LOWER(utm_term) LIKE 'leads%'    THEN 'leads'
      WHEN LOWER(utm_term) = 'basetotal'    THEN 'basetotal'
      ELSE 'other'
    END AS audience,
    SUM(revenue_brl) AS revenue_brl
  FROM fact_orders
  WHERE utm_content IS NOT NULL AND utm_content <> ''
  GROUP BY LOWER(utm_content),
    CASE
      WHEN LOWER(utm_term) LIKE 'clientes%' THEN 'clientes'
      WHEN LOWER(utm_term) LIKE 'leads%'    THEN 'leads'
      WHEN LOWER(utm_term) = 'basetotal'    THEN 'basetotal'
      ELSE 'other'
    END
) fo_seg ON fo_seg.utm_content = LOWER((regexp_match(da.name, '\[([a-zA-Z0-9]+)\]'))[1])
        AND (
          (da.name ~* '\[CLIENTES[^\]]*\]' AND fo_seg.audience = 'clientes')
          OR (da.name ~* '\[LEADS[^\]]*\]'  AND fo_seg.audience = 'leads')
          OR (da.name ~* '\[BASE[^\]]*\]'   AND fo_seg.audience = 'basetotal')
        )
LEFT JOIN (
  SELECT LOWER(utm_content) AS utm_content, SUM(revenue_brl) AS revenue_brl
  FROM fact_orders
  WHERE utm_content IS NOT NULL AND utm_content <> ''
  GROUP BY LOWER(utm_content)
) fo_tot ON fo_tot.utm_content = LOWER((regexp_match(da.name, '\[([a-zA-Z0-9]+)\]'))[1])
        AND da.name !~* '\[(CLIENTES|LEADS|BASE)[^\]]*\]'
GROUP BY da.id, da.name, da.type, da.is_active, dc.slug;

GRANT SELECT ON vw_email_asset_metrics TO anon;
