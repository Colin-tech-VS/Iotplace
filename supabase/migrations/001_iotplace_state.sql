-- Iotplace — initial persistence schema (Supabase / PostgreSQL)
-- Document store mirroring data/content.json for zero-downtime migration.
-- Future: split JSONB collections into normalized tables (enterprises, startups, …).

CREATE TABLE IF NOT EXISTS iotplace_state (
  id SMALLINT PRIMARY KEY DEFAULT 1,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT iotplace_state_singleton CHECK (id = 1)
);

CREATE INDEX IF NOT EXISTS idx_iotplace_state_updated ON iotplace_state (updated_at);

CREATE TABLE IF NOT EXISTS iotplace_schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO iotplace_schema_meta (key, value)
VALUES ('schema_version', '1')
ON CONFLICT (key) DO NOTHING;

GRANT SELECT, INSERT, UPDATE, DELETE ON iotplace_state TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON iotplace_schema_meta TO anon, authenticated, service_role;

-- Row Level Security: enable in Supabase dashboard when exposing tables via PostgREST.
-- ALTER TABLE iotplace_state ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE iotplace_schema_meta ENABLE ROW LEVEL SECURITY;
