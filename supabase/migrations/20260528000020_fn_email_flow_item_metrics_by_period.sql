-- Migration: função get_email_flow_item_metrics(p_start, p_end) com filtro de período
-- Reversível: sim (DROP FUNCTION get_email_flow_item_metrics(date, date))
--
-- Problema: vw_email_flow_item_metrics agrega dados de todos os tempos — o filtro
-- de período selecionado no dashboard não era aplicado aos e-mails individuais dos
-- fluxos, exibindo números all-time independente do período escolhido.
--
-- Correção: substituir a view por uma função SQL parametrizada. A função filtra
-- fact_email_sends.date >= p_start AND <= p_end antes de agregar.
-- Chamada no dashboard via supabase.rpc('get_email_flow_item_metrics', {p_start, p_end}).
--
-- Taxas calculadas: acumulado dentro do período (mesmo critério da vw_email_asset_metrics
-- para fluxos — disparo contínuo para novos inscritos, sem first-day).
-- CTOR retorna NULL quando clicks > opens (rastreamento de abertura sem $message).

CREATE OR REPLACE FUNCTION get_email_flow_item_metrics(p_start date, p_end date)
RETURNS TABLE(
  asset_id      uuid,
  item_id       uuid,
  item_name     text,
  item_position integer,
  is_active     boolean,
  sends         bigint,
  opens         bigint,
  clicks        bigint,
  bounces       bigint,
  unsubscribes  bigint,
  open_rate_pct numeric,
  ctor_pct      numeric
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    dai.asset_id,
    dai.id                                                                                          AS item_id,
    dai.name                                                                                        AS item_name,
    COALESCE(dai.position, 9999)                                                                    AS item_position,
    dai.is_active,
    SUM(fes.sends)                                                                                  AS sends,
    SUM(fes.opens)                                                                                  AS opens,
    SUM(fes.clicks)                                                                                 AS clicks,
    SUM(fes.bounces)                                                                                AS bounces,
    SUM(fes.unsubscribes)                                                                           AS unsubscribes,
    ROUND(SUM(fes.opens)::numeric  / NULLIF(SUM(fes.sends), 0)::numeric * 100, 2)                 AS open_rate_pct,
    CASE
      WHEN SUM(fes.opens) = 0 OR SUM(fes.clicks) > SUM(fes.opens) THEN NULL
      ELSE ROUND(SUM(fes.clicks)::numeric / SUM(fes.opens)::numeric * 100, 2)
    END                                                                                             AS ctor_pct
  FROM fact_email_sends fes
  JOIN dim_asset_items dai ON dai.id = fes.asset_item_id
  JOIN dim_assets      da  ON da.id  = dai.asset_id
  JOIN dim_channels    dc  ON dc.id  = da.channel_id
  WHERE dc.slug    = 'email_flow'
    AND dai.type   = 'email'
    AND fes.date  >= p_start
    AND fes.date  <= p_end
  GROUP BY dai.asset_id, dai.id, dai.name, dai.position, dai.is_active
  HAVING SUM(fes.sends) > 0
  ORDER BY dai.asset_id, COALESCE(dai.position, 9999), dai.name;

$$;

GRANT EXECUTE ON FUNCTION get_email_flow_item_metrics(date, date) TO anon;
