-- Migration: adiciona política de SELECT para role authenticated nas tabelas fact_* consultadas direto do frontend
-- Reversível: sim (DROP POLICY das 4 políticas criadas abaixo)
--
-- Contexto: o dashboard usa Supabase Auth (magic link). Uma vez logado, o supabase-js
-- passa a enviar o JWT do usuário nas consultas, e a role Postgres usada deixa de ser
-- "anon" e passa a ser "authenticated". As tabelas fact_* só tinham política de SELECT
-- para "anon" (o resto do dashboard sempre lê via views vw_*, que rodam como dono da
-- view e ignoram RLS — por isso o buraco nunca apareceu antes). A aba Recompra e o
-- card de Metas são os primeiros consumidores que leem fact_* direto, e por isso
-- quebraram: RLS filtrava tudo para role authenticated, devolvendo 0 linhas sem erro.
-- Esta política dá à role authenticated o mesmo acesso de leitura que anon já tem —
-- nenhum dado novo é exposto, apenas estendido a quem já passou pelo login por domínio.

CREATE POLICY authenticated_select_repurchase_monthly_metrics
  ON fact_repurchase_monthly_metrics FOR SELECT TO authenticated USING (true);

CREATE POLICY authenticated_select
  ON fact_monthly_goals FOR SELECT TO authenticated USING (true);

CREATE POLICY authenticated_select
  ON fact_orders FOR SELECT TO authenticated USING (true);

CREATE POLICY authenticated_select
  ON fact_lead_captures FOR SELECT TO authenticated USING (true);
