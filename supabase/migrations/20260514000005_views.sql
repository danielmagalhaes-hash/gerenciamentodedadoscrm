-- Migration 005 — Views (relatórios calculados)
-- Views são como "perguntas salvas": o dashboard as chama com um filtro de data
-- e o banco já devolve os números prontos — sem lógica de cálculo no JavaScript.
-- O dashboard SEMPRE deve passar WHERE date BETWEEN ... para não trazer todo o histórico.

-- ============================================================
-- vw_crm_daily_summary — Receita e sessões por canal por dia
-- Use: gráficos de tendência, tabela diária do dashboard
-- ============================================================
CREATE OR REPLACE VIEW vw_crm_daily_summary AS
SELECT
  d.date,
  dc.id                                                                       AS channel_id,
  dc.slug                                                                     AS channel_slug,
  dc.name                                                                     AS channel_name,
  -- pedidos
  COUNT(DISTINCT fo.order_id)                                                 AS purchases,
  COALESCE(SUM(fo.revenue_brl), 0)                                            AS revenue_brl,
  COALESCE(
    SUM(fo.revenue_brl) / NULLIF(COUNT(DISTINCT fo.order_id), 0),
    0
  )                                                                           AS avg_ticket_brl,
  COALESCE(SUM(CASE WHEN fo.is_first_purchase THEN fo.revenue_brl ELSE 0 END), 0)  AS revenue_first_purchase_brl,
  COALESCE(SUM(CASE WHEN NOT fo.is_first_purchase THEN fo.revenue_brl ELSE 0 END), 0) AS revenue_repurchase_brl,
  -- sessões
  COALESCE(fs.sessions,       0)                                              AS sessions,
  COALESCE(fs.add_to_cart,    0)                                              AS add_to_cart,
  COALESCE(fs.begin_checkout, 0)                                              AS begin_checkout,
  -- taxa de conversão (pedidos / sessões)
  COALESCE(
    COUNT(DISTINCT fo.order_id)::numeric / NULLIF(fs.sessions, 0),
    0
  )                                                                           AS conversion_rate
FROM (
  SELECT DISTINCT order_date AS date FROM fact_orders
  UNION
  SELECT DISTINCT date        FROM fact_sessions
) d
CROSS JOIN dim_channels dc
LEFT JOIN fact_orders   fo ON fo.attributed_channel_id = dc.id  AND fo.order_date = d.date
LEFT JOIN fact_sessions fs ON fs.channel_id            = dc.id  AND fs.date       = d.date
GROUP BY
  d.date, dc.id, dc.slug, dc.name,
  fs.sessions, fs.add_to_cart, fs.begin_checkout;

-- ============================================================
-- vw_channel_kpis — KPIs agregados por canal (filtrar por data via WHERE)
-- Use: cards de resumo por canal, ranking de canais
-- ============================================================
CREATE OR REPLACE VIEW vw_channel_kpis AS
SELECT
  dc.id                                                                        AS channel_id,
  dc.slug                                                                      AS channel_slug,
  dc.name                                                                      AS channel_name,
  COUNT(DISTINCT fo.order_id)                                                  AS purchases,
  COALESCE(SUM(fo.revenue_brl), 0)                                             AS revenue_brl,
  COALESCE(
    SUM(fo.revenue_brl) / NULLIF(COUNT(DISTINCT fo.order_id), 0),
    0
  )                                                                            AS avg_ticket_brl,
  COALESCE(
    SUM(fo.revenue_brl) / NULLIF(COUNT(DISTINCT fo.order_date), 0),
    0
  )                                                                            AS revenue_per_day,
  COALESCE(SUM(CASE WHEN fo.is_first_purchase     THEN fo.revenue_brl ELSE 0 END), 0) AS revenue_first_purchase_brl,
  COALESCE(SUM(CASE WHEN NOT fo.is_first_purchase THEN fo.revenue_brl ELSE 0 END), 0) AS revenue_repurchase_brl,
  COUNT(CASE WHEN fo.is_first_purchase     THEN 1 END)                         AS first_purchases,
  COUNT(CASE WHEN NOT fo.is_first_purchase THEN 1 END)                         AS repurchases
FROM dim_channels dc
LEFT JOIN fact_orders fo ON fo.attributed_channel_id = dc.id
GROUP BY dc.id, dc.slug, dc.name;

-- ============================================================
-- vw_asset_performance — Performance completa por ativo pai (fluxo/campanha)
-- Use: página de ativos, ranking de fluxos por receita
-- ============================================================
CREATE OR REPLACE VIEW vw_asset_performance AS
SELECT
  da.id                                                                        AS asset_id,
  da.name                                                                      AS asset_name,
  da.type                                                                      AS asset_type,
  da.source_tool,
  dc.id                                                                        AS channel_id,
  dc.slug                                                                      AS channel_slug,
  dc.name                                                                      AS channel_name,
  COUNT(DISTINCT dai.id)                                                       AS item_count,
  -- métricas de e-mail (agregadas dos itens filhos)
  COALESCE(SUM(fes.sends),           0)                                        AS email_sends,
  COALESCE(SUM(fes.opens),           0)                                        AS email_opens,
  COALESCE(SUM(fes.clicks),          0)                                        AS email_clicks,
  COALESCE(SUM(fes.unsubscribes),    0)                                        AS email_unsubscribes,
  COALESCE(SUM(fes.bounces),         0)                                        AS email_bounces,
  COALESCE(SUM(fes.spam_complaints), 0)                                        AS email_spam_complaints,
  COALESCE(SUM(fes.revenue_brl),     0)                                        AS email_revenue_brl,
  -- métricas de WhatsApp (agregadas dos itens filhos)
  COALESCE(SUM(fws.sends),           0)                                        AS wpp_sends,
  COALESCE(SUM(fws.read_count),      0)                                        AS wpp_reads,
  COALESCE(SUM(fws.replies),         0)                                        AS wpp_replies,
  COALESCE(SUM(fws.revenue_brl),     0)                                        AS wpp_revenue_brl,
  -- totais combinados
  COALESCE(SUM(fes.revenue_brl), 0) + COALESCE(SUM(fws.revenue_brl), 0)       AS total_revenue_brl,
  COALESCE(SUM(fes.sends), 0)       + COALESCE(SUM(fws.sends), 0)             AS total_sends,
  -- receita por disparo (RPS)
  CASE
    WHEN COALESCE(SUM(fes.sends), 0) + COALESCE(SUM(fws.sends), 0) > 0
    THEN (COALESCE(SUM(fes.revenue_brl), 0) + COALESCE(SUM(fws.revenue_brl), 0)) /
         (COALESCE(SUM(fes.sends), 0) + COALESCE(SUM(fws.sends), 0))
    ELSE 0
  END                                                                          AS revenue_per_send
FROM dim_assets da
JOIN dim_channels dc ON dc.id = da.channel_id
LEFT JOIN dim_asset_items  dai ON dai.asset_id     = da.id  AND dai.is_active = true
LEFT JOIN fact_email_sends fes ON fes.asset_item_id = dai.id
LEFT JOIN fact_wpp_sends   fws ON fws.asset_item_id = dai.id
GROUP BY da.id, da.name, da.type, da.source_tool, dc.id, dc.slug, dc.name;

-- ============================================================
-- vw_funnel_crm — Funil Sessões → ATC → BCO → Compras por canal
-- Use: visualização do funil de conversão por canal
-- ============================================================
CREATE OR REPLACE VIEW vw_funnel_crm AS
SELECT
  dc.id                                                                        AS channel_id,
  dc.slug                                                                      AS channel_slug,
  dc.name                                                                      AS channel_name,
  COALESCE(SUM(fs.sessions),       0)                                          AS sessions,
  COALESCE(SUM(fs.add_to_cart),    0)                                          AS add_to_cart,
  COALESCE(SUM(fs.begin_checkout), 0)                                          AS begin_checkout,
  COUNT(DISTINCT fo.order_id)                                                  AS purchases,
  -- taxas de conversão entre etapas
  COALESCE(SUM(fs.add_to_cart)::numeric    / NULLIF(SUM(fs.sessions),       0), 0) AS sessions_to_atc_rate,
  COALESCE(SUM(fs.begin_checkout)::numeric / NULLIF(SUM(fs.add_to_cart),    0), 0) AS atc_to_bco_rate,
  COALESCE(COUNT(DISTINCT fo.order_id)::numeric / NULLIF(SUM(fs.sessions),  0), 0) AS sessions_to_purchase_rate
FROM dim_channels dc
LEFT JOIN fact_sessions fs ON fs.channel_id            = dc.id
LEFT JOIN fact_orders   fo ON fo.attributed_channel_id = dc.id
GROUP BY dc.id, dc.slug, dc.name;

-- ============================================================
-- vw_leads_daily — Leads por dia por formulário
-- Use: página de captação, gráfico de leads por dia
-- ============================================================
CREATE OR REPLACE VIEW vw_leads_daily AS
SELECT
  flc.date,
  df.id                                                                        AS form_id,
  df.name                                                                      AS form_name,
  df.type                                                                      AS form_type,
  dc.id                                                                        AS channel_id,
  dc.slug                                                                      AS channel_slug,
  dc.name                                                                      AS channel_name,
  COALESCE(flc.impressions, 0)                                                 AS impressions,
  COALESCE(flc.submissions, 0)                                                 AS submissions,
  COALESCE(
    flc.submissions::numeric / NULLIF(flc.impressions, 0),
    0
  )                                                                            AS conversion_rate
FROM fact_lead_captures flc
JOIN  dim_forms    df ON df.id = flc.form_id
LEFT JOIN dim_channels dc ON dc.id = df.channel_id;

-- ============================================================
-- vw_pace_vs_goals — % atingido e status vs meta mensal
-- Use: painel de metas, indicador de ritmo do mês
-- ============================================================
CREATE OR REPLACE VIEW vw_pace_vs_goals AS
SELECT
  fmg.month,
  TO_CHAR(fmg.month, 'YYYY-MM')                                               AS month_label,
  fmg.goal_total_brl,
  fmg.goal_first_purchase_brl,
  fmg.goal_repurchase_brl,
  -- receita acumulada no mês
  COALESCE(rev.revenue_total,          0)                                      AS revenue_to_date,
  COALESCE(rev.revenue_first_purchase, 0)                                      AS revenue_first_purchase_to_date,
  COALESCE(rev.revenue_repurchase,     0)                                      AS revenue_repurchase_to_date,
  -- % atingido
  ROUND(
    COALESCE(rev.revenue_total, 0) / NULLIF(fmg.goal_total_brl, 0) * 100, 1
  )                                                                            AS pct_achieved,
  -- dias decorridos no mês (capped em hoje)
  -- subtração de duas datas no PostgreSQL retorna integer direto (dias)
  (LEAST(CURRENT_DATE, (fmg.month + '1 month'::interval - '1 day'::interval)::date)
    - fmg.month) + 1                                                           AS days_elapsed,
  -- total de dias no mês
  ((fmg.month + '1 month'::interval - '1 day'::interval)::date
    - fmg.month) + 1                                                           AS days_in_month,
  -- status: achieved / on_track / behind
  CASE
    WHEN COALESCE(rev.revenue_total, 0) >= fmg.goal_total_brl
      THEN 'achieved'
    WHEN fmg.goal_total_brl > 0
      AND COALESCE(rev.revenue_total, 0) / fmg.goal_total_brl >=
          ((LEAST(CURRENT_DATE, (fmg.month + '1 month'::interval - '1 day'::interval)::date) - fmg.month)::numeric + 1) /
          (((fmg.month + '1 month'::interval - '1 day'::interval)::date - fmg.month)::numeric + 1)
      THEN 'on_track'
    ELSE 'behind'
  END                                                                          AS status
FROM fact_monthly_goals fmg
LEFT JOIN (
  SELECT
    DATE_TRUNC('month', order_date)::date                                     AS month,
    SUM(revenue_brl)                                                           AS revenue_total,
    SUM(CASE WHEN is_first_purchase     THEN revenue_brl ELSE 0 END)          AS revenue_first_purchase,
    SUM(CASE WHEN NOT is_first_purchase THEN revenue_brl ELSE 0 END)          AS revenue_repurchase
  FROM fact_orders
  GROUP BY 1
) rev ON rev.month = fmg.month;

-- ============================================================
-- vw_email_health — Saúde da base de e-mail por canal
-- Use: página de saúde, alertas de bounce e spam
-- ============================================================
CREATE OR REPLACE VIEW vw_email_health AS
SELECT
  feh.date,
  dc.id                                                                        AS channel_id,
  dc.slug                                                                      AS channel_slug,
  dc.name                                                                      AS channel_name,
  feh.list_size,
  feh.active_subscribers,
  feh.bounced_total,
  feh.unsubscribed_total,
  -- taxa de base ativa (engajados 90d / total da lista)
  COALESCE(
    feh.active_subscribers::numeric / NULLIF(feh.list_size, 0),
    0
  )                                                                            AS active_rate
FROM fact_email_health feh
JOIN dim_channels dc ON dc.id = feh.channel_id;

-- ============================================================
-- GRANT SELECT nas views para a role anon (dashboard HTML)
-- ============================================================
GRANT SELECT ON vw_crm_daily_summary  TO anon;
GRANT SELECT ON vw_channel_kpis       TO anon;
GRANT SELECT ON vw_asset_performance  TO anon;
GRANT SELECT ON vw_funnel_crm         TO anon;
GRANT SELECT ON vw_leads_daily        TO anon;
GRANT SELECT ON vw_pace_vs_goals      TO anon;
GRANT SELECT ON vw_email_health       TO anon;
