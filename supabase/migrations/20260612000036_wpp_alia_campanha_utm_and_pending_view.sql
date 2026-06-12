-- Migration: adiciona utm_campaign em dim_wpp_alia_campanha_mapping e cria painel de conferência UTM
-- Reversível: sim (DROP COLUMN, DROP VIEW)

-- 1. Coluna utm_campaign na tabela de mapeamento de alia_campanha
ALTER TABLE dim_wpp_alia_campanha_mapping
  ADD COLUMN IF NOT EXISTS utm_campaign TEXT;

-- 2. Backfill: copia utm_campaign de dim_wpp_origem_mapping via flow_name
UPDATE dim_wpp_alia_campanha_mapping a
SET utm_campaign = (
  SELECT MIN(m.utm_campaign)
  FROM dim_wpp_origem_mapping m
  WHERE m.flow_name = a.flow_name
    AND m.utm_campaign IS NOT NULL
    AND m.is_ignored = false
)
WHERE a.flow_name IS NOT NULL
  AND a.utm_campaign IS NULL;

-- 3. Atualiza vw_wpp_flow_revenue para usar UNION DISTINCT dos dois mapeamentos
--    (evita dupla contagem caso o mesmo utm_campaign apareça nas duas tabelas)
DROP VIEW IF EXISTS vw_wpp_flow_revenue;
CREATE VIEW vw_wpp_flow_revenue AS
WITH utm_map AS (
  SELECT DISTINCT ON (utm_campaign) utm_campaign, flow_name
  FROM (
    SELECT utm_campaign, flow_name
    FROM dim_wpp_alia_campanha_mapping
    WHERE utm_campaign IS NOT NULL AND flow_name IS NOT NULL AND is_ignored = false
    UNION ALL
    SELECT utm_campaign, flow_name
    FROM dim_wpp_origem_mapping
    WHERE utm_campaign IS NOT NULL AND flow_name IS NOT NULL AND is_ignored = false
  ) combined
  ORDER BY utm_campaign
)
SELECT
  m.flow_name,
  o.order_date AS data,
  COUNT(*)           AS orders,
  SUM(o.revenue_brl) AS revenue_brl
FROM fact_orders o
JOIN dim_channels c   ON c.id = o.attributed_channel_id AND c.slug = 'wpp_flow'
JOIN utm_map m        ON m.utm_campaign = o.utm_campaign
GROUP BY m.flow_name, o.order_date;

GRANT SELECT ON vw_wpp_flow_revenue TO anon;

-- 4. View de pendências UTM para o painel de conferência do dashboard
DROP VIEW IF EXISTS vw_wpp_flow_utm_pending;
CREATE VIEW vw_wpp_flow_utm_pending AS
-- Alia campanha configurada mas sem utm_campaign ou sem flow_name
SELECT 'alia_campanha'::text AS source_type,
       alia_campanha         AS key_value,
       flow_name
FROM dim_wpp_alia_campanha_mapping
WHERE is_ignored = false
  AND (utm_campaign IS NULL OR flow_name IS NULL)
UNION ALL
-- Alia campanha completamente nova (ainda não está na tabela de mapeamento)
SELECT 'alia_campanha', value, NULL::text
FROM vw_wpp_flow_unknown WHERE source = 'alia_campanha'
UNION ALL
-- Origem com flow_name mas sem utm_campaign
SELECT 'origem', origem, flow_name
FROM dim_wpp_origem_mapping
WHERE is_ignored = false AND utm_campaign IS NULL
UNION ALL
-- Origem completamente nova (ainda não está na tabela de mapeamento)
SELECT 'origem', value, NULL::text
FROM vw_wpp_flow_unknown WHERE source = 'leads';

GRANT SELECT ON vw_wpp_flow_utm_pending TO anon;
