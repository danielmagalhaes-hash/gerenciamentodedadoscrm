-- Migration: aumenta o statement_timeout da function de refresh das materialized views
-- Reversível: sim
--   CREATE OR REPLACE FUNCTION refresh_repurchase_materialized_views() ... (sem o SET statement_timeout)
--
-- Contexto: chamar essa function via RPC (PostgREST) usa o statement_timeout padrão
-- da role, curto demais para um REFRESH MATERIALIZED VIEW sobre ~470 mil linhas
-- (estourava com "canceling statement due to statement timeout"). SET statement_timeout
-- na própria function dá mais tempo só para ela, sem mexer no timeout padrão do resto da API.

CREATE OR REPLACE FUNCTION refresh_repurchase_materialized_views()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout = '5min'
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_repurchase_deals_dedup;
    REFRESH MATERIALIZED VIEW mv_repurchase_customer_first_purchase;
END;
$$;

GRANT EXECUTE ON FUNCTION refresh_repurchase_materialized_views() TO service_role;
