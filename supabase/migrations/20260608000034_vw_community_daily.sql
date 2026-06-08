-- Migration: vw_community_daily — métricas diárias do canal wpp_community
-- Reversível: sim — DROP VIEW IF EXISTS vw_community_daily;

CREATE OR REPLACE VIEW vw_community_daily AS
WITH channel AS (
    SELECT id FROM dim_channels WHERE slug = 'wpp_community'
),
actions_daily AS (
    SELECT
        action_date                                            AS date,
        COUNT(*) FILTER (WHERE success = true)::bigint        AS sends_count
    FROM fact_community_actions
    WHERE channel_id = (SELECT id FROM channel)
    GROUP BY action_date
),
analytics_daily AS (
    SELECT
        date,
        SUM(members_added)::bigint    AS members_added,
        SUM(members_removed)::bigint  AS members_removed,
        SUM(link_clicks)::bigint      AS link_clicks,
        MAX(total_members)            AS total_members
    FROM fact_community_analytics
    WHERE channel_id = (SELECT id FROM channel)
    GROUP BY date
),
revenue_daily AS (
    SELECT
        order_date                    AS date,
        SUM(revenue_brl)::numeric     AS revenue_brl,
        COUNT(order_id)::bigint       AS orders
    FROM fact_orders
    WHERE attributed_channel_id = (SELECT id FROM channel)
    GROUP BY order_date
),
all_dates AS (
    SELECT date FROM actions_daily
    UNION
    SELECT date FROM analytics_daily
    UNION
    SELECT date FROM revenue_daily
)
SELECT
    d.date,
    'wpp_community'                           AS channel_slug,
    COALESCE(ac.sends_count, 0)               AS sends_count,
    COALESCE(an.members_added, 0)             AS members_added,
    COALESCE(an.members_removed, 0)           AS members_removed,
    an.total_members,
    COALESCE(an.link_clicks, 0)               AS link_clicks,
    COALESCE(r.revenue_brl, 0)                AS revenue_brl,
    COALESCE(r.orders, 0)                     AS orders,
    CASE
        WHEN COALESCE(ac.sends_count, 0) > 0
        THEN COALESCE(r.revenue_brl, 0) / ac.sends_count::numeric
        ELSE NULL
    END                                       AS revenue_per_send
FROM all_dates d
LEFT JOIN actions_daily   ac ON ac.date = d.date
LEFT JOIN analytics_daily an ON an.date = d.date
LEFT JOIN revenue_daily    r ON r.date  = d.date
ORDER BY d.date;

GRANT SELECT ON vw_community_daily TO anon;
GRANT SELECT ON vw_community_daily TO authenticated;
