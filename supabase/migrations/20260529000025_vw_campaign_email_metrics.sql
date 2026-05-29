-- Migration: view vw_campaign_email_metrics — substitui vw_email_asset_metrics para campanhas
-- Fonte: campaign_email_metrics (ingestão via API Klaviyo) em vez de fact_email_sends
-- Reversível: sim — DROP VIEW vw_campaign_email_metrics;
-- Mesma interface de colunas de vw_email_asset_metrics para compatibilidade com o dashboard

CREATE OR REPLACE VIEW vw_campaign_email_metrics AS
SELECT
  cem.campaign_id                                                                        AS asset_id,
  cem.campaign_name                                                                      AS asset_name,
  'campaign'                                                                             AS asset_type,
  COALESCE(da.is_active, true)                                                           AS is_active,
  'email_campaign'                                                                       AS channel_slug,
  MIN(cem.data)                                                                          AS first_date,
  MAX(cem.data)                                                                          AS last_date,
  MIN(cem.data)                                                                          AS send_date,
  SUM(cem.email_enviado)                                                                 AS sends,
  SUM(cem.email_aberto)                                                                  AS opens,
  SUM(cem.email_clicado)                                                                 AS clicks,
  0                                                                                      AS bounces,
  0                                                                                      AS unsubscribes,
  ROUND(SUM(cem.email_aberto)::numeric  / NULLIF(SUM(cem.email_enviado), 0) * 100, 2)  AS open_rate_pct,
  ROUND(SUM(cem.email_clicado)::numeric / NULLIF(SUM(cem.email_aberto),  0) * 100, 2)  AS ctor_pct,
  ROUND(SUM(cem.email_enviado)::numeric / NULLIF(COUNT(DISTINCT cem.data), 0), 1)       AS sends_per_day,
  COALESCE(MAX(fo_seg.revenue_brl), 0)                                                  AS revenue_brl,
  ROUND(
    COALESCE(MAX(fo_seg.revenue_brl), 0) / NULLIF(SUM(cem.email_enviado), 0),
    4
  )                                                                                      AS revenue_per_send

FROM campaign_email_metrics cem

-- Status da campanha no dim_assets (opcional — fallback true se não encontrado)
LEFT JOIN dim_assets da
  ON  da.external_id  = cem.campaign_id
  AND da.source_tool  = 'klaviyo'
  AND da.type         = 'campaign'

-- Receita atribuída via utm_content (mesmo critério de vw_email_asset_metrics)
LEFT JOIN (
  SELECT
    LOWER(utm_content) AS utm_content,
    CASE
      WHEN LOWER(utm_term) LIKE '%clientes%' THEN 'clientes'
      WHEN LOWER(utm_term) LIKE '%leads%'    THEN 'leads'
      ELSE                                        'basetotal'
    END AS audience,
    SUM(revenue_brl) AS revenue_brl
  FROM fact_orders
  WHERE utm_content IS NOT NULL AND utm_content <> ''
  GROUP BY
    LOWER(utm_content),
    CASE
      WHEN LOWER(utm_term) LIKE '%clientes%' THEN 'clientes'
      WHEN LOWER(utm_term) LIKE '%leads%'    THEN 'leads'
      ELSE                                        'basetotal'
    END
) fo_seg
  ON  fo_seg.utm_content = LOWER((regexp_match(cem.campaign_name, '\[([a-zA-Z0-9]+)\]'))[1])
  AND fo_seg.audience = CASE
    WHEN cem.campaign_name ~* '\[CLIENTES[^\]]*\]' THEN 'clientes'
    WHEN cem.campaign_name ~* '\[LEADS[^\]]*\]'    THEN 'leads'
    ELSE                                                 'basetotal'
  END

GROUP BY cem.campaign_id, cem.campaign_name, da.is_active;

GRANT SELECT ON vw_campaign_email_metrics TO anon;
