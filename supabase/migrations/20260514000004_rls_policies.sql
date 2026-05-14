-- Migration 004 — Políticas de acesso (RLS)
-- "RLS" funciona como um porteiro em cada gaveta do banco:
--   - a chave anon (usada pelo dashboard HTML) só pode ler (SELECT)
--   - a chave service_role (usada pelo Python) ignora o porteiro e pode ler e escrever
-- Habilitar RLS sem criar política de leitura para anon bloquearia o dashboard.

-- ============================================================
-- Habilita RLS em todas as tabelas
-- ============================================================
ALTER TABLE dim_channels         ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_assets           ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_asset_items      ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_forms            ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_utm_mappings     ENABLE ROW LEVEL SECURITY;

ALTER TABLE fact_orders          ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_sessions        ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_email_sends     ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_wpp_sends       ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_wpp_subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_community_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_community_sends ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_lead_captures   ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_email_health    ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_monthly_goals   ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Políticas de leitura para a role anon (dashboard HTML)
-- USING (true) = todos os registros são visíveis
-- ============================================================
CREATE POLICY "anon_select" ON dim_channels         FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON dim_assets           FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON dim_asset_items      FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON dim_forms            FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON dim_utm_mappings     FOR SELECT TO anon USING (true);

CREATE POLICY "anon_select" ON fact_orders          FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_sessions        FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_email_sends     FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_wpp_sends       FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_wpp_subscribers FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_community_members FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_community_sends FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_lead_captures   FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_email_health    FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select" ON fact_monthly_goals   FOR SELECT TO anon USING (true);

-- ============================================================
-- GRANT explícito de SELECT para anon em todas as tabelas
-- (Supabase exige tanto RLS policy quanto GRANT para liberar acesso)
-- ============================================================
GRANT SELECT ON dim_channels          TO anon;
GRANT SELECT ON dim_assets            TO anon;
GRANT SELECT ON dim_asset_items       TO anon;
GRANT SELECT ON dim_forms             TO anon;
GRANT SELECT ON dim_utm_mappings      TO anon;

GRANT SELECT ON fact_orders           TO anon;
GRANT SELECT ON fact_sessions         TO anon;
GRANT SELECT ON fact_email_sends      TO anon;
GRANT SELECT ON fact_wpp_sends        TO anon;
GRANT SELECT ON fact_wpp_subscribers  TO anon;
GRANT SELECT ON fact_community_members TO anon;
GRANT SELECT ON fact_community_sends  TO anon;
GRANT SELECT ON fact_lead_captures    TO anon;
GRANT SELECT ON fact_email_health     TO anon;
GRANT SELECT ON fact_monthly_goals    TO anon;

-- Nota: a role service_role contorna o RLS automaticamente no Supabase.
-- Não é necessário criar políticas de escrita para ela.
