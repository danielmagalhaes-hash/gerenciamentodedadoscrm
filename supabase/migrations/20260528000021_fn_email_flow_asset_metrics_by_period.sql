-- Migration: função get_email_flow_asset_metrics(p_start, p_end) com filtro de período
-- Reversível: sim (DROP FUNCTION get_email_flow_asset_metrics(date, date))
--
-- Problema: vw_email_asset_metrics agrega dados all-time para fluxos — o período
-- selecionado no dashboard não era aplicado à tabela pai de fluxos (apenas os
-- itens drill-down passaram a filtrar após migration 20).
--
-- Correção: função SQL parametrizada que filtra fact_email_sends.date pelo
-- período antes de agregar. Não inclui revenue (coluna não exibida na tabela
-- de fluxos). Chamada via supabase.rpc('get_email_flow_asset_metrics', {...}).
--
-- Taxas: acumulado dentro do período (disparo contínuo para novos inscritos).
-- CTOR retorna NULL quando clicks > opens (mesmo critério das migrations 18-19).

CREATE OR REPLACE FUNCTION get_email_flow_asset_metrics(p_start date, p_end date)
RETURNS TABLE(
  asset_id      uuid,
  asset_name    text,
  asset_type    text,
  is_active     boolean,
  sends         bigint,
  opens         bigint,
  clicks        bigint,
  bounces       bigint,
  unsubscribes  bigint,
  open_rate_pct numeric,
  ctor_pct      numeric,
  sends_per_day numeric
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    da.id                                                                                        AS asset_id,
    da.name                                                                                      AS asset_name,
    da.type                                                                                      AS asset_type,
    da.is_active,
    SUM(fes.sends)                                                                               AS sends,
    SUM(fes.opens)                                                                               AS opens,
    SUM(fes.clicks)                                                                              AS clicks,
    SUM(fes.bounces)                                                                             AS bounces,
    SUM(fes.unsubscribes)                                                                        AS unsubscribes,
    ROUND(SUM(fes.opens)::numeric / NULLIF(SUM(fes.sends), 0)::numeric * 100, 2)               AS open_rate_pct,
    CASE
      WHEN SUM(fes.opens) = 0 OR SUM(fes.clicks) > SUM(fes.opens) THEN NULL
      ELSE ROUND(SUM(fes.clicks)::numeric / SUM(fes.opens)::numeric * 100, 2)
    END                                                                                          AS ctor_pct,
    ROUND(SUM(fes.sends)::numeric / NULLIF(COUNT(DISTINCT fes.date), 0)::numeric, 1)           AS sends_per_day
  FROM fact_email_sends fes
  JOIN dim_asset_items  dai ON dai.id = fes.asset_item_id
  JOIN dim_assets       da  ON da.id  = dai.asset_id
  JOIN dim_channels     dc  ON dc.id  = da.channel_id
  WHERE dc.slug  = 'email_flow'
    AND dai.type = 'email'
    AND fes.date >= p_start
    AND fes.date <= p_end
  GROUP BY da.id, da.name, da.type, da.is_active
  HAVING SUM(fes.sends) > 0
  ORDER BY SUM(fes.sends) DESC;
$$;

GRANT EXECUTE ON FUNCTION get_email_flow_asset_metrics(date, date) TO anon;
