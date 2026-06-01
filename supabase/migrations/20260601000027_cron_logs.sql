-- Migration: tabela cron_logs para registrar execuções dos cron jobs
-- Reversível: sim — DROP TABLE cron_logs;

CREATE TABLE IF NOT EXISTS cron_logs (
    id         uuid        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    job        text        NOT NULL,
    status     text        NOT NULL CHECK (status IN ('ok', 'error')),
    message    text,
    ran_at     timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE cron_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon pode ler cron_logs"
    ON cron_logs FOR SELECT TO anon USING (true);

CREATE POLICY "service_role pode gravar cron_logs"
    ON cron_logs FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX idx_cron_logs_ran_at ON cron_logs (ran_at DESC);
CREATE INDEX idx_cron_logs_status ON cron_logs (status);
