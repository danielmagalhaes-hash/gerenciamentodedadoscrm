-- Migration: fact_community_actions + fact_community_analytics — canal wpp_community via Sendflow
-- Reversível: sim
--   DROP TABLE IF EXISTS fact_community_actions;
--   DROP TABLE IF EXISTS fact_community_analytics;

-- 1. Ações de disparo da comunidade (um registro por ação sendMessages no Sendflow)
CREATE TABLE IF NOT EXISTS fact_community_actions (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    action_id    text        NOT NULL UNIQUE,
    release_id   text        NOT NULL,
    asset_id     uuid        REFERENCES dim_assets(id),
    channel_id   uuid        NOT NULL REFERENCES dim_channels(id),
    action_date  date        NOT NULL,
    action_type  text        NOT NULL,
    success      boolean,
    scheduled_to timestamptz,
    finished_at  timestamptz,
    ingested_at  timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE fact_community_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_select_community_actions"
    ON fact_community_actions FOR SELECT TO anon USING (true);

CREATE POLICY "service_role_all_community_actions"
    ON fact_community_actions FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_community_actions_date    ON fact_community_actions (action_date);
CREATE INDEX IF NOT EXISTS idx_community_actions_asset   ON fact_community_actions (asset_id);
CREATE INDEX IF NOT EXISTS idx_community_actions_release ON fact_community_actions (release_id);

-- 2. Analytics de crescimento por release por dia (entradas, saídas, cliques no link)
CREATE TABLE IF NOT EXISTS fact_community_analytics (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    date            date        NOT NULL,
    release_id      text        NOT NULL,
    asset_id        uuid        REFERENCES dim_assets(id),
    channel_id      uuid        NOT NULL REFERENCES dim_channels(id),
    members_added   integer     NOT NULL DEFAULT 0,
    members_removed integer     NOT NULL DEFAULT 0,
    link_clicks     integer     NOT NULL DEFAULT 0,
    total_members   integer,
    ingested_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (date, release_id)
);

ALTER TABLE fact_community_analytics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_select_community_analytics"
    ON fact_community_analytics FOR SELECT TO anon USING (true);

CREATE POLICY "service_role_all_community_analytics"
    ON fact_community_analytics FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_community_analytics_date    ON fact_community_analytics (date);
CREATE INDEX IF NOT EXISTS idx_community_analytics_asset   ON fact_community_analytics (asset_id);
CREATE INDEX IF NOT EXISTS idx_community_analytics_release ON fact_community_analytics (release_id);
