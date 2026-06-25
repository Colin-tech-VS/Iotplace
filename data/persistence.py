"""Pluggable persistence: JSON file (dev) or PostgreSQL (prod / Supabase)."""

from __future__ import annotations

import copy
import json
import os
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_backend: "StateBackend | None" = None
_process_cache: dict[str, Any] | None = None
_process_cache_version: str | None = None
# Short in-process TTL on the state-version probe. Within this window a warm
# cache is served without re-querying the backend for `updated_at`, collapsing
# the per-request DB round-trip on hot paths (page loads, the 20s nav poll).
# Writes in *this* worker refresh the cache immediately (see save_state /
# mutate_state), so the author always sees their own change; another worker may
# serve reads up to STATE_VERSION_TTL seconds stale — acceptable for this app.
STATE_VERSION_TTL = float(os.environ.get("IOTPLACE_STATE_VERSION_TTL", "2.5"))
_version_checked_at: float = 0.0
_pools: dict[str, Any] = {}
_schema_ready_urls: set[str] = set()
_supabase_clients: dict[tuple[str, str], Any] = {}

DATA_DIR = Path(__file__).parent
DEFAULT_JSON_FILE = DATA_DIR / "content.json"
SEED_JSON_FILE = DATA_DIR / "content.seed.json"


def resolve_data_file() -> Path:
    custom = (os.environ.get("IOTPLACE_DATA_DIR") or "").strip()
    if custom:
        path = Path(custom)
        path.mkdir(parents=True, exist_ok=True)
        return path / "content.json"
    return DEFAULT_JSON_FILE


def _supabase_project_ref() -> str:
    explicit = (os.environ.get("SUPABASE_PROJECT_REF") or "").strip()
    if explicit:
        return explicit
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    if url.endswith(".supabase.co"):
        return url.rsplit("//", 1)[-1].removesuffix(".supabase.co")
    return ""


def _build_supabase_db_url() -> str:
    password = (os.environ.get("SUPABASE_DB_PASSWORD") or "").strip()
    if not password:
        return ""
    ref = _supabase_project_ref()
    if not ref:
        return ""
    from urllib.parse import quote_plus

    host = (os.environ.get("SUPABASE_DB_HOST") or "aws-1-eu-central-1.pooler.supabase.com").strip()
    port = (os.environ.get("SUPABASE_DB_PORT") or "6543").strip()
    user = (os.environ.get("SUPABASE_DB_USER") or f"postgres.{ref}").strip()
    dbname = (os.environ.get("SUPABASE_DB_NAME") or "postgres").strip()
    return f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{dbname}"


def resolve_database_url() -> str:
    raw = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("SUPABASE_DB_URL")
        or os.environ.get("IOTPLACE_DATABASE_URL")
        or _build_supabase_db_url()
        or ""
    ).strip()
    if raw.startswith("postgres://"):
        return "postgresql://" + raw[len("postgres://") :]
    return raw


def resolve_supabase_rest_config() -> tuple[str, str] | None:
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (
        os.environ.get("SUPABASE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
        or os.environ.get("SUPABASE_PUBLISHABLE_KEY")
        or ""
    ).strip()
    if url and key:
        return url, key
    return None


def resolve_backend_name() -> str:
    explicit = (os.environ.get("IOTPLACE_DATA_BACKEND") or "auto").strip().lower()
    if explicit in ("json", "postgres", "supabase"):
        return explicit
    if resolve_database_url():
        return "postgres"
    if resolve_supabase_rest_config():
        return "supabase"
    return "json"


class StateBackend(ABC):
    @abstractmethod
    def load(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def save(self, data: dict[str, Any]) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError


class JsonFileBackend(StateBackend):
    def __init__(self, path: Path | None = None):
        self.path = path or resolve_data_file()

    @property
    def name(self) -> str:
        return "json"

    def get_state_version(self) -> str:
        if self.path.exists():
            return str(int(self.path.stat().st_mtime_ns))
        return ""

    def load(self) -> dict[str, Any]:
        with _lock:
            if not self.path.exists():
                seed = _read_seed_document()
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self._write_file(seed)
                return seed.copy()
            try:
                with open(self.path, encoding="utf-8") as handle:
                    return json.load(handle)
            except json.JSONDecodeError:
                backup = self.path.with_suffix(".json.bak")
                if self.path.stat().st_size > 0:
                    self.path.replace(backup)
                seed = _read_seed_document()
                self._write_file(seed)
                return seed.copy()

    def save(self, data: dict[str, Any]) -> None:
        with _lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._write_file(data)

    def _write_file(self, data: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        tmp.replace(self.path)


class SupabaseRestBackend(StateBackend):
    def __init__(self, url: str | None = None, key: str | None = None):
        config = resolve_supabase_rest_config()
        if not config and not (url and key):
            raise RuntimeError("SUPABASE_URL et SUPABASE_KEY requis pour le backend Supabase.")
        self.url, self.key = (url, key) if url and key else config  # type: ignore[misc]
        self.client = _get_supabase_client(self.url, self.key)

    @property
    def name(self) -> str:
        return "supabase"

    def get_state_version(self) -> str:
        result = (
            self.client.table("iotplace_state")
            .select("updated_at")
            .eq("id", 1)
            .limit(1)
            .execute()
        )
        if result.data:
            return str(result.data[0].get("updated_at") or "")
        return ""

    def load(self) -> dict[str, Any]:
        with _lock:
            result = (
                self.client.table("iotplace_state")
                .select("data")
                .eq("id", 1)
                .limit(1)
                .execute()
            )
            if result.data:
                payload = result.data[0].get("data")
                if isinstance(payload, dict):
                    return payload.copy()
                if payload is not None:
                    return json.loads(payload)

            seed = _read_seed_document()
            self.save(seed)
            return seed.copy()

    def save(self, data: dict[str, Any]) -> None:
        with _lock:
            self.client.table("iotplace_state").upsert(
                {"id": 1, "data": data},
                on_conflict="id",
            ).execute()


def _get_supabase_client(url: str, key: str):
    cache_key = (url, key)
    if cache_key not in _supabase_clients:
        from supabase import create_client

        _supabase_clients[cache_key] = create_client(url, key)
    return _supabase_clients[cache_key]


def _get_connection_pool(database_url: str):
    if database_url not in _pools:
        from psycopg_pool import ConnectionPool

        # `check` validates a connection before it leaves the pool, and
        # `max_idle` recycles connections Supabase's pooler silently drops
        # after a short idle period. Without these, the first query after the
        # app sits idle (e.g. a login) gets handed a dead connection and the
        # request 500s with an OperationalError.
        _pools[database_url] = ConnectionPool(
            database_url,
            min_size=1,
            max_size=8,
            timeout=10,
            max_idle=120,
            max_lifetime=600,
            check=ConnectionPool.check_connection,
            reconnect_timeout=10,
            kwargs={"prepare_threshold": None},
            open=True,
        )
    return _pools[database_url]


def _is_stale_connection_error(exc: Exception) -> bool:
    """True for errors that mean 'the connection died' — safe to retry once."""
    import psycopg

    if isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    # psycopg_pool raises PoolTimeout when it can't hand out a live connection.
    return exc.__class__.__name__ in {"PoolTimeout", "ConnectionTimeout"}


class PostgresBackend(StateBackend):
    SCHEMA_VERSION = "1"

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or resolve_database_url()
        if not self.database_url:
            raise RuntimeError("DATABASE_URL manquant pour le backend PostgreSQL.")

    @property
    def name(self) -> str:
        return "postgres"

    def get_state_version(self) -> str:
        pool = _get_connection_pool(self.database_url)
        with pool.connection() as conn:
            row = conn.execute(
                "SELECT updated_at FROM iotplace_state WHERE id = 1"
            ).fetchone()
            if row and row[0] is not None:
                return str(row[0])
        return ""

    def _with_connection(self, work):
        """Run `work(conn)` with one automatic retry if the connection is stale.

        Supabase's connection pooler can drop a connection between requests; the
        first query then fails with OperationalError. Retrying once with a fresh
        connection turns those transient blips into a successful request instead
        of a 500.
        """
        pool = _get_connection_pool(self.database_url)
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                with _lock:
                    with pool.connection() as conn:
                        return work(conn)
            except Exception as exc:  # noqa: BLE001 — re-raised below if not stale
                last_exc = exc
                if attempt == 0 and _is_stale_connection_error(exc):
                    import logging

                    logging.warning(
                        "Postgres connection stale (%s); retrying once.",
                        exc.__class__.__name__,
                    )
                    continue
                raise
        if last_exc:
            raise last_exc

    def load(self) -> dict[str, Any]:
        from psycopg.types.json import Jsonb

        def work(conn):
            if self.database_url not in _schema_ready_urls:
                self._ensure_schema(conn)
                conn.commit()
                _schema_ready_urls.add(self.database_url)

            row = conn.execute(
                "SELECT data FROM iotplace_state WHERE id = 1"
            ).fetchone()
            if row and row[0]:
                payload = row[0]
                return payload.copy() if isinstance(payload, dict) else json.loads(payload)

            seed = _read_seed_document()
            conn.execute(
                """
                INSERT INTO iotplace_state (id, data, updated_at)
                VALUES (1, %s, NOW())
                ON CONFLICT (id) DO UPDATE
                SET data = EXCLUDED.data, updated_at = NOW()
                """,
                (Jsonb(seed),),
            )
            conn.commit()
            return seed.copy()

        return self._with_connection(work)

    def save(self, data: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb

        def work(conn):
            if self.database_url not in _schema_ready_urls:
                self._ensure_schema(conn)
                _schema_ready_urls.add(self.database_url)
            conn.execute(
                """
                INSERT INTO iotplace_state (id, data, updated_at)
                VALUES (1, %s, NOW())
                ON CONFLICT (id) DO UPDATE
                SET data = EXCLUDED.data, updated_at = NOW()
                """,
                (Jsonb(data),),
            )
            conn.commit()

        self._with_connection(work)

    # Advisory-lock key (arbitrary constant) used to serialize state writes
    # across workers/processes for the singleton state row.
    STATE_LOCK_KEY = 718281828

    def mutate(self, mutator):
        from psycopg.types.json import Jsonb

        def work(conn):
            if self.database_url not in _schema_ready_urls:
                self._ensure_schema(conn)
                _schema_ready_urls.add(self.database_url)
            # Serialize concurrent writers: held until COMMIT below.
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (self.STATE_LOCK_KEY,))
            row = conn.execute(
                "SELECT data FROM iotplace_state WHERE id = 1"
            ).fetchone()
            if row and row[0]:
                payload = row[0]
                data = payload.copy() if isinstance(payload, dict) else json.loads(payload)
            else:
                data = _read_seed_document()

            result = mutator(data)

            conn.execute(
                """
                INSERT INTO iotplace_state (id, data, updated_at)
                VALUES (1, %s, NOW())
                ON CONFLICT (id) DO UPDATE
                SET data = EXCLUDED.data, updated_at = NOW()
                """,
                (Jsonb(data),),
            )
            conn.commit()
            return result, data

        return self._with_connection(work)

    def _ensure_schema(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS iotplace_state (
              id SMALLINT PRIMARY KEY DEFAULT 1,
              data JSONB NOT NULL DEFAULT '{}'::jsonb,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              CONSTRAINT iotplace_state_singleton CHECK (id = 1)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS iotplace_schema_meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.execute(
            """
            INSERT INTO iotplace_schema_meta (key, value)
            VALUES ('schema_version', %s)
            ON CONFLICT (key) DO NOTHING
            """,
            (self.SCHEMA_VERSION,),
        )
        self._harden_privileges(conn)

    def _harden_privileges(self, conn) -> None:
        """Least privilege for the singleton state blob (emails, password hashes,
        messages, payment refs). The app connects as the table owner via
        DATABASE_URL and owners bypass RLS, so this never blocks the app — but it
        denies access to Supabase's public PostgREST roles (anon/authenticated),
        closing the 'entire DB readable via the public anon key' exposure.

        Best-effort: a failure (e.g. not the table owner) is logged, not fatal."""
        try:
            with conn.transaction():
                conn.execute("ALTER TABLE iotplace_state ENABLE ROW LEVEL SECURITY")
                conn.execute("ALTER TABLE iotplace_schema_meta ENABLE ROW LEVEL SECURITY")
                conn.execute(
                    """
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
                    """
                )
        except Exception:  # noqa: BLE001 — hardening is best-effort, never fatal
            import logging

            logging.warning(
                "iotplace: DB privilege hardening skipped (insufficient rights?)",
                exc_info=True,
            )


def _read_seed_document() -> dict[str, Any]:
    for candidate in (resolve_data_file(), DEFAULT_JSON_FILE, SEED_JSON_FILE):
        if candidate.exists():
            with open(candidate, encoding="utf-8") as handle:
                return json.load(handle)
    from data.store import DEFAULT_DATA

    return DEFAULT_DATA.copy()


def get_backend() -> StateBackend:
    global _backend
    if _backend is not None:
        return _backend

    name = resolve_backend_name()
    if name == "postgres":
        _backend = PostgresBackend()
    elif name == "supabase":
        _backend = SupabaseRestBackend()
    else:
        _backend = JsonFileBackend()
    return _backend


def invalidate_state_cache() -> None:
    global _process_cache, _process_cache_version, _version_checked_at
    with _lock:
        _process_cache = None
        _process_cache_version = None
        _version_checked_at = 0.0


def _backend_state_version(backend: StateBackend) -> str:
    if hasattr(backend, "get_state_version"):
        try:
            return backend.get_state_version()
        except Exception:
            return ""
    if isinstance(backend, JsonFileBackend):
        path = backend.path
        if path.exists():
            return str(int(path.stat().st_mtime_ns))
    return ""


def load_state() -> dict[str, Any]:
    global _process_cache, _process_cache_version, _version_checked_at

    backend = get_backend()

    # Fast path: a warm cache whose version was probed within the TTL window is
    # served without touching the backend at all (no `updated_at` round-trip).
    with _lock:
        if (
            _process_cache is not None
            and _process_cache_version
            and (time.monotonic() - _version_checked_at) < STATE_VERSION_TTL
        ):
            return copy.deepcopy(_process_cache)

    version = _backend_state_version(backend)

    with _lock:
        if _process_cache is not None and _process_cache_version == version and version:
            _version_checked_at = time.monotonic()
            return copy.deepcopy(_process_cache)

    data = backend.load()

    with _lock:
        _process_cache = data
        _process_cache_version = version or "loaded"
        _version_checked_at = time.monotonic()

    return copy.deepcopy(data)


def save_state(data: dict[str, Any]) -> None:
    global _process_cache, _process_cache_version, _version_checked_at

    backend = get_backend()
    backend.save(data)
    with _lock:
        _process_cache = copy.deepcopy(data)
        _process_cache_version = _backend_state_version(backend) or "saved"
        _version_checked_at = time.monotonic()


def mutate_state(mutator):
    """Atomic read-modify-write of the whole state, returning (result, data).

    ``mutator(data)`` edits ``data`` in place and returns the caller's result.
    On Postgres (production) the read, mutation and write run inside a single
    transaction guarded by a session advisory lock, so two Gunicorn workers can
    never both load the same snapshot and overwrite each other (lost update).
    JSON (dev, single process) and the Supabase REST backend are serialized by
    the in-process lock.
    """
    global _process_cache, _process_cache_version, _version_checked_at
    backend = get_backend()

    if isinstance(backend, PostgresBackend):
        result, data = backend.mutate(mutator)
    else:
        with _lock:
            data = backend.load()
            result = mutator(data)
            backend.save(data)

    with _lock:
        _process_cache = copy.deepcopy(data)
        _process_cache_version = _backend_state_version(backend) or "saved"
        _version_checked_at = time.monotonic()
    return result, data


def persistence_info() -> dict[str, str]:
    backend = get_backend()
    info = {"backend": backend.name}
    if backend.name == "json" and isinstance(backend, JsonFileBackend):
        info["path"] = str(backend.path)
    if backend.name == "postgres":
        info["database"] = "configured"
    if backend.name == "supabase":
        info["database"] = "supabase-rest"
        ref = _supabase_project_ref()
        if ref:
            info["project"] = ref
    return info
