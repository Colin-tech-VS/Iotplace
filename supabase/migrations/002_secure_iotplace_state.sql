-- Iotplace — security hardening for databases provisioned with the original
-- 001 migration, which granted the public `anon`/`authenticated` PostgREST roles
-- full read/write on the state blob (emails, password hashes, messages, payment
-- refs). Run this once in the Supabase SQL Editor on any existing project.
--
-- The app connects as the table owner via DATABASE_URL (SUPABASE_DB_PASSWORD),
-- and owners bypass RLS, so this never blocks the application. It only removes
-- access for the public anon key and turns on Row Level Security (no policies =
-- PostgREST denied). The Flask app also re-applies this automatically on boot
-- (see data/persistence.py: PostgresBackend._harden_privileges).

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    REVOKE ALL ON iotplace_state FROM anon;
    REVOKE ALL ON iotplace_schema_meta FROM anon;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    REVOKE ALL ON iotplace_state FROM authenticated;
    REVOKE ALL ON iotplace_schema_meta FROM authenticated;
  END IF;
END
$$;

ALTER TABLE iotplace_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE iotplace_schema_meta ENABLE ROW LEVEL SECURITY;
