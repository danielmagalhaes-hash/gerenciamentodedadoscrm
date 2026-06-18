-- Migration: mapeia origem "Up-sell Perpetuo" para o fluxo Up-Sell Perpetuo
-- Reversível: sim (DELETE FROM dim_wpp_origem_mapping WHERE origem = 'Up-sell Perpetuo')

-- O fluxo foi renomeado na Vekta de "Up-sell Perpetuo - Camiseta" para "Up-sell Perpetuo".
-- Sem este mapeamento, 1.974 leads chegavam na leads_webhook mas ficavam invisíveis
-- na vw_wpp_flow_leads porque a view faz JOIN exato por origem.
INSERT INTO dim_wpp_origem_mapping (origem, flow_name, utm_campaign, is_ignored)
VALUES ('Up-sell Perpetuo', 'Up-Sell Perpetuo', 'upsell_imediato', false)
ON CONFLICT (origem) DO UPDATE
  SET flow_name    = EXCLUDED.flow_name,
      utm_campaign = EXCLUDED.utm_campaign,
      is_ignored   = EXCLUDED.is_ignored;
