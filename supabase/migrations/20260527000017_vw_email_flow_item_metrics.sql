-- Migration: view de métricas por e-mail individual dentro de fluxos (drill-down)
-- Reversível: sim (DROP VIEW vw_email_flow_item_metrics)
--
-- Propósito: suportar o detalhamento de cada fluxo de e-mail no dashboard.
-- Quando o usuário clica em um fluxo na tabela, expande os e-mails individuais
-- com suas métricas agregadas (disparos, aberturas, cliques, taxa de abertura, CTOR).
--
-- Taxas calculadas usando apenas o primeiro dia de disparo (mesmo critério de
-- vw_email_asset_metrics) para evitar inflação por Apple MPP.

CREATE VIEW vw_email_flow_item_metrics AS
WITH item_send_date AS (
  -- Primeiro dia com disparos > 0 por item
  SELECT
    fes.asset_item_id,
    MIN(fes.date) FILTER (WHERE fes.sends > 0) AS send_date
  FROM fact_email_sends fes
  GROUP BY fes.asset_item_id
),
item_first_day AS (
  -- Aberturas e cliques somente no dia do primeiro disparo
  SELECT
    fes.asset_item_id,
    SUM(fes.opens)  AS opens_d1,
    SUM(fes.clicks) AS clicks_d1
  FROM fact_email_sends fes
  JOIN item_send_date isd ON isd.asset_item_id = fes.asset_item_id
                          AND fes.date = isd.send_date
  GROUP BY fes.asset_item_id
)
SELECT
  dai.asset_id,
  dai.id                                                                                       AS item_id,
  dai.name                                                                                     AS item_name,
  COALESCE(dai.position, 9999)                                                                 AS position,
  dai.is_active,
  SUM(fes.sends)                                                                               AS sends,
  SUM(fes.opens)                                                                               AS opens,
  SUM(fes.clicks)                                                                              AS clicks,
  SUM(fes.bounces)                                                                             AS bounces,
  SUM(fes.unsubscribes)                                                                        AS unsubscribes,
  ROUND(COALESCE(ifd.opens_d1,  0)::numeric / NULLIF(SUM(fes.sends), 0)::numeric * 100, 2)   AS open_rate_pct,
  ROUND(COALESCE(ifd.clicks_d1, 0)::numeric / NULLIF(COALESCE(ifd.opens_d1, 0), 0)::numeric * 100, 2) AS ctor_pct
FROM fact_email_sends fes
JOIN dim_asset_items dai ON dai.id = fes.asset_item_id
JOIN dim_assets      da  ON da.id  = dai.asset_id
JOIN dim_channels    dc  ON dc.id  = da.channel_id
LEFT JOIN item_first_day ifd ON ifd.asset_item_id = fes.asset_item_id
WHERE dc.slug = 'email_flow'
  AND dai.type = 'email'
GROUP BY dai.asset_id, dai.id, dai.name, dai.position, dai.is_active, ifd.opens_d1, ifd.clicks_d1
HAVING SUM(fes.sends) > 0;

GRANT SELECT ON vw_email_flow_item_metrics TO anon;
