-- Migration: corrige fan-out em vw_community_daily
-- Reversível: sim (DROP VIEW + recriar versão anterior)
-- Causa: JOIN direto de fact_community_actions e fact_orders multiplicava linhas,
--        inflando sends_count pelo número de pedidos do mesmo dia.
-- Solução: CTEs pré-agregam cada fonte antes do JOIN final.

DROP VIEW IF EXISTS vw_community_daily;

CREATE VIEW vw_community_daily AS
WITH daily_actions AS (
  SELECT
    action_date                   AS date,
    channel_id,
    SUM((success)::int)           AS sends_count
  FROM fact_community_actions
  GROUP BY action_date, channel_id
),
daily_analytics AS (
  SELECT
    date,
    channel_id,
    SUM(members_added)            AS members_added,
    SUM(members_removed)          AS members_removed,
    SUM(link_clicks)              AS link_clicks,
    MAX(total_members)            AS total_members,
    MAX(total_groups)             AS total_groups
  FROM fact_community_analytics
  GROUP BY date, channel_id
),
daily_orders AS (
  SELECT
    o.order_date                  AS date,
    o.attributed_channel_id       AS channel_id,
    COUNT(DISTINCT o.order_id)    AS orders,
    SUM(o.revenue_brl)            AS revenue_brl
  FROM fact_orders o
  JOIN dim_channels ch ON ch.id = o.attributed_channel_id
  WHERE ch.slug = 'wpp_community'
  GROUP BY o.order_date, o.attributed_channel_id
),
all_dates AS (
  SELECT date FROM daily_actions
  UNION
  SELECT date FROM daily_analytics
  UNION
  SELECT date FROM daily_orders
)
SELECT
  d.date,
  ch.slug                                             AS channel_slug,
  COALESCE(a.sends_count,    0)                       AS sends_count,
  COALESCE(an.members_added,    0)                    AS members_added,
  COALESCE(an.members_removed,  0)                    AS members_removed,
  an.total_members,
  an.total_groups,
  COALESCE(an.link_clicks,   0)                       AS link_clicks,
  COALESCE(o.revenue_brl,    0)                       AS revenue_brl,
  COALESCE(o.orders,         0)                       AS orders,
  CASE WHEN COALESCE(a.sends_count, 0) > 0
       THEN o.revenue_brl / a.sends_count
       ELSE NULL END                                  AS revenue_per_send
FROM all_dates d
CROSS JOIN (SELECT id, slug FROM dim_channels WHERE slug = 'wpp_community') ch
LEFT JOIN daily_actions   a  ON a.date  = d.date AND a.channel_id  = ch.id
LEFT JOIN daily_analytics an ON an.date = d.date AND an.channel_id = ch.id
LEFT JOIN daily_orders    o  ON o.date  = d.date AND o.channel_id  = ch.id
ORDER BY d.date;

GRANT SELECT ON vw_community_daily TO anon;
