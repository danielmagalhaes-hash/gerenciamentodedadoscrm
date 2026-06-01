-- Migration: E-mail Fluxo passa a ler de flow_email_metrics em vez de fact_email_sends
-- Motivo: flow_email_metrics tem histórico completo desde mar/2026 (6.811 linhas, 24 fluxos)
--         fact_email_sends tinha apenas 205 linhas desde abr/2026
-- Reversível: sim — recriar funções e view lendo de fact_email_sends

CREATE OR REPLACE FUNCTION get_email_flow_asset_metrics(p_start date, p_end date)
RETURNS TABLE(
  asset_id uuid, asset_name text, asset_type text, is_active boolean,
  sends bigint, opens bigint, clicks bigint, bounces bigint, unsubscribes bigint,
  open_rate_pct numeric, ctor_pct numeric, sends_per_day numeric
)
LANGUAGE sql STABLE AS $$
  SELECT
    da.id, fem.flow_name, 'flow'::text, COALESCE(da.is_active, true),
    SUM(fem.email_enviado)::bigint, SUM(fem.email_aberto)::bigint, SUM(fem.email_clicado)::bigint,
    0::bigint, 0::bigint,
    ROUND(SUM(fem.email_aberto)::numeric / NULLIF(SUM(fem.email_enviado),0) * 100, 2),
    CASE WHEN SUM(fem.email_aberto)=0 OR SUM(fem.email_clicado)>SUM(fem.email_aberto) THEN NULL
         ELSE ROUND(SUM(fem.email_clicado)::numeric / SUM(fem.email_aberto) * 100, 2) END,
    ROUND(SUM(fem.email_enviado)::numeric / NULLIF(COUNT(DISTINCT fem.data),0), 1)
  FROM flow_email_metrics fem
  LEFT JOIN dim_assets da ON da.external_id=fem.flow_id AND da.source_tool='klaviyo' AND da.type='flow'
  WHERE fem.data >= p_start AND fem.data <= p_end
  GROUP BY da.id, da.is_active, fem.flow_id, fem.flow_name
  ORDER BY SUM(fem.email_enviado) DESC, fem.flow_name;
$$;

CREATE OR REPLACE FUNCTION get_email_flow_item_metrics(p_start date, p_end date)
RETURNS TABLE(
  asset_id uuid, item_id uuid, item_name text, item_position integer, is_active boolean,
  sends bigint, opens bigint, clicks bigint, bounces bigint, unsubscribes bigint,
  open_rate_pct numeric, ctor_pct numeric
)
LANGUAGE sql STABLE AS $$
  SELECT
    da.id, dai.id, COALESCE(dai.name, fem.message_name), COALESCE(dai.position, 9999),
    COALESCE(dai.is_active, true),
    SUM(fem.email_enviado)::bigint, SUM(fem.email_aberto)::bigint, SUM(fem.email_clicado)::bigint,
    0::bigint, 0::bigint,
    ROUND(SUM(fem.email_aberto)::numeric / NULLIF(SUM(fem.email_enviado),0) * 100, 2),
    CASE WHEN SUM(fem.email_aberto)=0 THEN NULL
         ELSE ROUND(SUM(fem.email_clicado)::numeric / SUM(fem.email_aberto) * 100, 2) END
  FROM flow_email_metrics fem
  LEFT JOIN dim_asset_items dai ON dai.external_id=fem.message_id AND dai.type='email'
  LEFT JOIN dim_assets da ON da.external_id=fem.flow_id AND da.source_tool='klaviyo' AND da.type='flow'
  WHERE fem.data >= p_start AND fem.data <= p_end
  GROUP BY da.id, dai.id, dai.name, dai.position, dai.is_active, fem.message_id, fem.message_name
  HAVING SUM(fem.email_enviado) > 0
  ORDER BY da.id NULLS LAST, COALESCE(dai.position,9999), COALESCE(dai.name, fem.message_name);
$$;

CREATE OR REPLACE VIEW vw_email_channel_daily AS
SELECT
    fem.data                                                                                   AS date,
    dc.slug                                                                                    AS channel_slug,
    dc.name                                                                                    AS channel_name,
    SUM(fem.email_enviado)::bigint                                                             AS sends,
    SUM(fem.email_aberto)::bigint                                                              AS opens,
    SUM(fem.email_clicado)::bigint                                                             AS clicks,
    0::bigint                                                                                  AS bounces,
    0::bigint                                                                                  AS unsubscribes,
    ROUND(SUM(fem.email_aberto)::numeric / NULLIF(SUM(fem.email_enviado),0) * 100, 2)         AS open_rate_pct,
    ROUND(SUM(fem.email_clicado)::numeric / NULLIF(SUM(fem.email_aberto),0) * 100, 2)         AS ctor_pct,
    MAX(fem.updated_at)::timestamptz                                                           AS ingested_at
FROM flow_email_metrics fem
CROSS JOIN (SELECT slug, name FROM dim_channels WHERE slug = 'email_flow') dc
GROUP BY fem.data, dc.slug, dc.name

UNION ALL

SELECT
    cem.data                                                                                   AS date,
    dc.slug                                                                                    AS channel_slug,
    dc.name                                                                                    AS channel_name,
    SUM(cem.email_enviado)::bigint                                                             AS sends,
    SUM(cem.email_aberto)::bigint                                                              AS opens,
    SUM(cem.email_clicado)::bigint                                                             AS clicks,
    0::bigint                                                                                  AS bounces,
    0::bigint                                                                                  AS unsubscribes,
    ROUND(SUM(cem.email_aberto)::numeric / NULLIF(SUM(cem.email_enviado),0) * 100, 2)         AS open_rate_pct,
    ROUND(SUM(cem.email_clicado)::numeric / NULLIF(SUM(cem.email_aberto),0) * 100, 2)         AS ctor_pct,
    MAX(cem.updated_at)::timestamptz                                                           AS ingested_at
FROM campaign_email_metrics cem
CROSS JOIN (SELECT slug, name FROM dim_channels WHERE slug = 'email_campaign') dc
GROUP BY cem.data, dc.slug, dc.name;

GRANT SELECT ON vw_email_channel_daily TO anon;
