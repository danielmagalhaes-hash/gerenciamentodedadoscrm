-- Migration: utm_term em flow_utm_config + views de receita por fluxo e e-mail
-- Reversível: sim — DROP VIEW vw_flow_email_revenue; DROP VIEW vw_flow_item_revenue;
--             ALTER TABLE flow_utm_config DROP COLUMN utm_term;

-- 1. Adiciona utm_term ao flow_utm_config
--    NULL = qualquer term (fluxos com múltiplas audiências, ex: Welcome)
--    Valor = term específico (fluxos que compartilham utm_campaign, ex: MOF, Retenção)
ALTER TABLE flow_utm_config ADD COLUMN IF NOT EXISTS utm_term text;

-- 2. Popula utm_term para fluxos MOF (compartilham utm_campaign = 'fluxotof')
UPDATE flow_utm_config SET utm_term = 'jeans'       WHERE flow_name = '[Fluxo] Fluxo MOF - Jeans Novos - Novo Modelo 2026';
UPDATE flow_utm_config SET utm_term = 'camiseta t'  WHERE flow_name = '[Fluxo] Fluxo MOF - Camiseta T - Novo Modelo 2026';
UPDATE flow_utm_config SET utm_term = 'c3l4'        WHERE flow_name = '[Fluxo] Fluxo MOF - Compre 3 e Leve 4 - Novo Modelo 2026';
UPDATE flow_utm_config SET utm_term = 'c3l4 brinde' WHERE flow_name = '[Fluxo] Fluxo MOF - Compre 3 e Leve 4 + Brinde - Novo Modelo 2026';
UPDATE flow_utm_config SET utm_term = 'comfort'     WHERE flow_name = '[Fluxo] Fluxo MOF - Comfort - Novo Modelo 2026';
UPDATE flow_utm_config SET utm_term = 'polo'        WHERE flow_name = '[Fluxo] Fluxo MOF - Polo - Novo Modelo 2026';

-- 3. Popula utm_term para fluxos de Retenção (compartilham utm_campaign = 'retencao')
--    Nota: '180 _dias' (com espaço) é o valor real nos pedidos, não o da planilha ('180+_dias')
UPDATE flow_utm_config SET utm_term = '0-60_dias'    WHERE flow_name = '[Fluxo] [Retenção] - 21 - 60 DIAS';
UPDATE flow_utm_config SET utm_term = '60-90_dias'   WHERE flow_name = '[Fluxo] [Retenção] - 60 - 90 DIAS';
UPDATE flow_utm_config SET utm_term = '90-120_dias'  WHERE flow_name = '[Fluxo] [Retenção] - 90 - 120 DIAS';
UPDATE flow_utm_config SET utm_term = '120-150_dias' WHERE flow_name = '[Fluxo] [Retenção] 120-150D';
UPDATE flow_utm_config SET utm_term = '150-180_dias' WHERE flow_name = '[Fluxo] [Retenção] 150-180D';
UPDATE flow_utm_config SET utm_term = '180 _dias'    WHERE flow_name = '[Fluxo] [Retenção] 180-210D';

-- 4. View de receita por fluxo por dia
--    Lógica: utm_term NULL no config = aceita qualquer term nos pedidos (ex: Welcome aceita leads + clientes)
--            utm_term preenchido = só pedidos com aquele term exato
CREATE OR REPLACE VIEW vw_flow_email_revenue AS
SELECT
  fuc.flow_name,
  fo.order_date,
  SUM(fo.revenue_brl)::numeric  AS revenue_brl,
  COUNT(fo.order_id)::bigint    AS orders
FROM flow_utm_config fuc
JOIN fact_orders fo ON
  fo.utm_source = 'email'
  AND fo.utm_medium IN ('email_fluxo', 'fluxos_crm')
  AND fo.utm_campaign = fuc.utm_campaign
  AND (fuc.utm_term IS NULL OR fo.utm_term = fuc.utm_term)
GROUP BY fuc.flow_name, fo.order_date;

GRANT SELECT ON vw_flow_email_revenue TO anon;
GRANT SELECT ON vw_flow_email_revenue TO authenticated;

-- 5. View de receita por e-mail individual (via utm_content)
CREATE OR REPLACE VIEW vw_flow_item_revenue AS
SELECT
  fo.utm_campaign,
  fo.utm_term,
  fo.utm_content,
  fo.order_date,
  SUM(fo.revenue_brl)::numeric  AS revenue_brl,
  COUNT(fo.order_id)::bigint    AS orders
FROM fact_orders fo
WHERE fo.utm_source = 'email'
  AND fo.utm_medium IN ('email_fluxo', 'fluxos_crm')
  AND fo.utm_content IS NOT NULL
  AND fo.utm_content != ''
GROUP BY fo.utm_campaign, fo.utm_term, fo.utm_content, fo.order_date;

GRANT SELECT ON vw_flow_item_revenue TO anon;
GRANT SELECT ON vw_flow_item_revenue TO authenticated;

-- 6. Recria vw_flow_email_assets com utm_term exposto
CREATE OR REPLACE VIEW vw_flow_email_assets AS
SELECT
  fem.flow_id,
  fem.flow_name,
  fem.data,
  SUM(fem.email_enviado)::bigint  AS sends,
  SUM(fem.email_aberto)::bigint   AS opens,
  SUM(fem.email_clicado)::bigint  AS clicks,
  fuc.utm_campaign,
  fuc.utm_term
FROM flow_email_metrics fem
LEFT JOIN flow_utm_config fuc ON fuc.flow_name = fem.flow_name
GROUP BY fem.flow_id, fem.flow_name, fem.data, fuc.utm_campaign, fuc.utm_term;

GRANT SELECT ON vw_flow_email_assets TO anon;
GRANT SELECT ON vw_flow_email_assets TO authenticated;

-- 7. Recria vw_flow_email_items com utm_campaign e utm_term (necessário para atribuição por e-mail)
CREATE OR REPLACE VIEW vw_flow_email_items AS
SELECT
  fem.flow_id,
  fem.message_id,
  fem.message_name,
  fem.data,
  fem.email_enviado::bigint  AS sends,
  fem.email_aberto::bigint   AS opens,
  fem.email_clicado::bigint  AS clicks,
  fuc.utm_campaign,
  fuc.utm_term
FROM flow_email_metrics fem
LEFT JOIN flow_utm_config fuc ON fuc.flow_name = fem.flow_name;

GRANT SELECT ON vw_flow_email_items TO anon;
GRANT SELECT ON vw_flow_email_items TO authenticated;
