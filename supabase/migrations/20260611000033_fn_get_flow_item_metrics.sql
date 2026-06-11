-- Migration: função que agrega métricas de e-mails de fluxo por período
-- Reversível: sim — DROP FUNCTION get_flow_item_metrics(date, date);
--
-- Motivo: vw_flow_email_items retorna 1 linha por (message_id, data).
-- Com 30 dias × centenas de mensagens o resultado ultrapassa o limite de
-- linhas da API do Supabase (max_rows), fazendo o dashboard receber apenas
-- uma fração dos dados e exibir inscritos incorretos (ex: 4.691 em vez de 26.765).
-- Esta função agrega no banco e retorna 1 linha por mensagem — ~350 linhas no total.

CREATE OR REPLACE FUNCTION get_flow_item_metrics(start_date date, end_date date)
RETURNS TABLE (
  flow_id      text,
  message_id   text,
  message_name text,
  utm_campaign text,
  utm_term     text,
  sends        bigint,
  opens        bigint,
  clicks       bigint
)
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT
    fem.flow_id,
    fem.message_id,
    fem.message_name,
    fuc.utm_campaign,
    fuc.utm_term,
    SUM(fem.email_enviado)::bigint AS sends,
    SUM(fem.email_aberto)::bigint  AS opens,
    SUM(fem.email_clicado)::bigint AS clicks
  FROM flow_email_metrics fem
  LEFT JOIN flow_utm_config fuc ON fuc.flow_name = fem.flow_name
  WHERE fem.data >= start_date
    AND fem.data <= end_date
  GROUP BY fem.flow_id, fem.message_id, fem.message_name,
           fuc.utm_campaign, fuc.utm_term;
$$;

GRANT EXECUTE ON FUNCTION get_flow_item_metrics(date, date) TO anon;
GRANT EXECUTE ON FUNCTION get_flow_item_metrics(date, date) TO authenticated;
