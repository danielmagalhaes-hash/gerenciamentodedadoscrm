-- Migration: adiciona metas por canal em fact_monthly_goals
-- Reversível: sim (DROP COLUMN IF EXISTS nas colunas novas; ADD NOT NULL de volta nas antigas)

-- Remove constraint que exigia first_purchase + repurchase = total
-- (colunas passam a ser opcionais no novo fluxo centrado em canal)
ALTER TABLE fact_monthly_goals
  DROP CONSTRAINT IF EXISTS fact_monthly_goals_goal_total_brl_check;

ALTER TABLE fact_monthly_goals
  ALTER COLUMN goal_first_purchase_brl DROP NOT NULL,
  ALTER COLUMN goal_repurchase_brl     DROP NOT NULL;

-- Metas por canal (nullable — preenchidas via popup no dashboard)
ALTER TABLE fact_monthly_goals
  ADD COLUMN IF NOT EXISTS goal_email_flow_brl      numeric(12,2),
  ADD COLUMN IF NOT EXISTS goal_email_campaign_brl  numeric(12,2),
  ADD COLUMN IF NOT EXISTS goal_wpp_flow_brl        numeric(12,2),
  ADD COLUMN IF NOT EXISTS goal_wpp_campaign_brl    numeric(12,2),
  ADD COLUMN IF NOT EXISTS goal_community_brl       numeric(12,2);
