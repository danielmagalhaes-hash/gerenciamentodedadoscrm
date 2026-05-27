-- Migration: versão final de vw_email_asset_metrics com send_date e case-insensitive utm_content
-- Reversível: sim (recriar versão anterior)
-- Supersede: 20260527000011 (corrige send_date para MIN e LOWER no JOIN de utm_content)
--
-- Correções em relação à 000011:
--   - send_date = MIN(CASE WHEN sends > 0 THEN date END): data de início do disparo
--   - LOWER() no JOIN: emails têm [EM1250] mas orders têm utm_content = 'em1250'

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
  COALESCE(MAX(fo_agg.revenue_brl), 0)                                              AS revenue_brl,
  ROUND(
    COALESCE(MAX(fo_agg.revenue_brl), 0) / NULLIF(SUM(fes.sends), 0),
    4
  )                                                                                  AS revenue_per_send
FROM fact_email_sends fes
JOIN dim_asset_items  dai ON dai.id = fes.asset_item_id
JOIN dim_assets       da  ON da.id  = dai.asset_id
JOIN dim_channels     dc  ON dc.id  = da.channel_id
LEFT JOIN (
  SELECT LOWER(utm_content) AS utm_content, SUM(revenue_brl) AS revenue_brl
  FROM fact_orders
  WHERE utm_content IS NOT NULL AND utm_content <> ''
  GROUP BY LOWER(utm_content)
) fo_agg ON fo_agg.utm_content = LOWER((regexp_match(da.name, '\[([a-zA-Z0-9]+)\]'))[1])
GROUP BY da.id, da.name, da.type, da.is_active, dc.slug;

GRANT SELECT ON vw_email_asset_metrics TO anon;
