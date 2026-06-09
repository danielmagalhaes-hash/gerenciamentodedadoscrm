-- Migration: adiciona total_groups em fact_community_analytics e atualiza vw_community_daily
-- Reversível: sim (DROP COLUMN IF EXISTS; CREATE OR REPLACE VIEW)

ALTER TABLE fact_community_analytics
  ADD COLUMN IF NOT EXISTS total_groups integer;

-- Atualiza view para expor total_members e total_groups no snapshot atual
CREATE OR REPLACE VIEW vw_community_daily AS
SELECT
  d.date,
  ch.slug                               AS channel_slug,
  COALESCE(SUM(a.success::int), 0)      AS sends_count,
  COALESCE(SUM(an.members_added), 0)    AS members_added,
  COALESCE(SUM(an.members_removed), 0)  AS members_removed,
  MAX(an.total_members)                 AS total_members,
  MAX(an.total_groups)                  AS total_groups,
  COALESCE(SUM(an.link_clicks), 0)      AS link_clicks,
  COALESCE(SUM(o.revenue_brl), 0)       AS revenue_brl,
  COUNT(DISTINCT o.order_id)            AS orders,
  CASE WHEN COALESCE(SUM(a.success::int), 0) > 0
       THEN COALESCE(SUM(o.revenue_brl), 0) / SUM(a.success::int)
       ELSE NULL END                    AS revenue_per_send
FROM (
  SELECT DISTINCT date FROM (
    SELECT action_date AS date FROM fact_community_actions
    UNION
    SELECT date        FROM fact_community_analytics
    UNION
    SELECT order_date  FROM fact_orders fo
      JOIN dim_channels dc ON dc.id = fo.attributed_channel_id
     WHERE dc.slug = 'wpp_community'
  ) x
) d
CROSS JOIN (SELECT id, slug FROM dim_channels WHERE slug = 'wpp_community') ch
LEFT JOIN fact_community_actions a
       ON a.action_date = d.date
      AND a.channel_id = ch.id
      AND a.success = true
LEFT JOIN fact_community_analytics an
       ON an.date = d.date
      AND an.channel_id = ch.id
LEFT JOIN fact_orders o
       ON o.order_date = d.date
      AND o.attributed_channel_id = ch.id
GROUP BY d.date, ch.slug
ORDER BY d.date;
