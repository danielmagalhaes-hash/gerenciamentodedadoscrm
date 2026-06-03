-- Migration: views de suporte para E-mail Fluxo — assets e items por dia
-- Reversível: sim — DROP VIEW vw_flow_email_assets; DROP VIEW vw_flow_email_items;
--
-- Motivo: queries diretas a flow_email_metrics via supabase-js retornam vazio no browser.
-- Views rodam como owner (postgres), contornando o problema. Segue R11: views no banco.

CREATE OR REPLACE VIEW vw_flow_email_assets AS
SELECT
  fem.flow_id,
  fem.flow_name,
  fem.data,
  SUM(fem.email_enviado)::bigint  AS sends,
  SUM(fem.email_aberto)::bigint   AS opens,
  SUM(fem.email_clicado)::bigint  AS clicks,
  fuc.utm_campaign
FROM flow_email_metrics fem
LEFT JOIN flow_utm_config fuc ON fuc.flow_name = fem.flow_name
GROUP BY fem.flow_id, fem.flow_name, fem.data, fuc.utm_campaign;

GRANT SELECT ON vw_flow_email_assets TO anon;
GRANT SELECT ON vw_flow_email_assets TO authenticated;

CREATE OR REPLACE VIEW vw_flow_email_items AS
SELECT
  fem.flow_id,
  fem.message_id,
  fem.message_name,
  fem.data,
  fem.email_enviado::bigint  AS sends,
  fem.email_aberto::bigint   AS opens,
  fem.email_clicado::bigint  AS clicks
FROM flow_email_metrics fem;

GRANT SELECT ON vw_flow_email_items TO anon;
GRANT SELECT ON vw_flow_email_items TO authenticated;
