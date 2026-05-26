-- Migration: adiciona view vw_form_performance — totais de captação por formulário
-- Reversível: sim (DROP VIEW vw_form_performance)

-- ============================================================
-- vw_form_performance — Totais históricos de captação por formulário
-- Use: tabela "Formulários e Popups · Performance de captação" no dashboard
-- ============================================================
CREATE OR REPLACE VIEW vw_form_performance AS
SELECT
  df.id                                                                         AS form_id,
  df.name                                                                       AS form_name,
  df.type                                                                       AS form_type,
  df.is_active,
  dc.id                                                                         AS channel_id,
  dc.slug                                                                       AS channel_slug,
  dc.name                                                                       AS channel_name,
  COALESCE(SUM(flc.impressions), 0)                                             AS total_impressions,
  COALESCE(SUM(flc.submissions), 0)                                             AS total_submissions,
  COALESCE(
    SUM(flc.submissions)::numeric / NULLIF(SUM(flc.impressions), 0),
    0
  )                                                                             AS signup_rate,
  MAX(flc.ingested_at)                                                          AS ingested_at
FROM dim_forms df
LEFT JOIN dim_channels dc ON dc.id = df.channel_id
LEFT JOIN fact_lead_captures flc ON flc.form_id = df.id
GROUP BY df.id, df.name, df.type, df.is_active, dc.id, dc.slug, dc.name;

GRANT SELECT ON vw_form_performance TO anon;
