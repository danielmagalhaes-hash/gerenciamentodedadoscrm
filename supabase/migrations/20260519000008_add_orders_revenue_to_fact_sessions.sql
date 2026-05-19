-- Migration: adiciona orders e revenue_brl às tabelas fact_sessions e fact_sessions_utm
-- Reversível: sim (DROP COLUMN IF EXISTS)

ALTER TABLE fact_sessions
    ADD COLUMN IF NOT EXISTS orders      integer        NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS revenue_brl numeric(12,2)  NOT NULL DEFAULT 0;

ALTER TABLE fact_sessions_utm
    ADD COLUMN IF NOT EXISTS orders      integer        NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS revenue_brl numeric(12,2)  NOT NULL DEFAULT 0;
