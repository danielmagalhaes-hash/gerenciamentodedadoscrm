-- Migration: disparos diários de EM001 por período (opcional: filtro por flow_id)
-- Reversível: sim — DROP FUNCTION get_daily_em001_sends(date, date, text);
--
-- Uso: gráfico Receita/Inscrito por dia no E-mail Fluxo
--   sem p_flow_id → soma todos os fluxos (visão de canal)
--   com p_flow_id → apenas o fluxo selecionado no filtro

CREATE OR REPLACE FUNCTION get_daily_em001_sends(
  start_date date,
  end_date   date,
  p_flow_id  text DEFAULT NULL
)
RETURNS TABLE (data date, sends bigint)
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT
    fem.data,
    SUM(fem.email_enviado)::bigint AS sends
  FROM flow_email_metrics fem
  WHERE fem.data >= start_date
    AND fem.data <= end_date
    AND fem.message_name ILIKE '%EM001%'
    AND (p_flow_id IS NULL OR fem.flow_id = p_flow_id)
  GROUP BY fem.data
  ORDER BY fem.data;
$$;

GRANT EXECUTE ON FUNCTION get_daily_em001_sends(date, date, text) TO anon;
GRANT EXECUTE ON FUNCTION get_daily_em001_sends(date, date, text) TO authenticated;
