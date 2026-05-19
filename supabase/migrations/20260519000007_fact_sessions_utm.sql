-- Migration: adiciona fact_sessions_utm para dados granulares por UTM (sessões/ATC/BCO)
-- Reversível: sim — DROP TABLE fact_sessions_utm;

CREATE TABLE IF NOT EXISTS fact_sessions_utm (
    id              uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    date            date          NOT NULL,
    channel_id      uuid          NOT NULL REFERENCES dim_channels(id),
    utm_source      text          NOT NULL DEFAULT '',
    utm_medium      text          NOT NULL DEFAULT '',
    utm_campaign    text          NOT NULL DEFAULT '',
    utm_term        text          NOT NULL DEFAULT '',
    utm_content     text          NOT NULL DEFAULT '',
    sessions        integer       NOT NULL DEFAULT 0,
    add_to_cart     integer       NOT NULL DEFAULT 0,
    begin_checkout  integer       NOT NULL DEFAULT 0,
    ingested_at     timestamptz   NOT NULL DEFAULT now(),

    CONSTRAINT fact_sessions_utm_unique
        UNIQUE (date, channel_id, utm_source, utm_medium, utm_campaign, utm_term, utm_content)
);

ALTER TABLE fact_sessions_utm ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_select" ON fact_sessions_utm
    FOR SELECT TO anon USING (true);

CREATE POLICY "service_all" ON fact_sessions_utm
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX fact_sessions_utm_date_idx     ON fact_sessions_utm (date);
CREATE INDEX fact_sessions_utm_channel_idx  ON fact_sessions_utm (channel_id);
CREATE INDEX fact_sessions_utm_campaign_idx ON fact_sessions_utm (utm_campaign);
