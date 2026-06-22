"""Pluggable persistence: JSON file (dev) or PostgreSQL (prod / Supabase)."""

from __future__ import annotations

import json
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_backend: "StateBackend | None" = None

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
        from supabase import create_client

        self.client = create_client(self.url, self.key)

    @property
    def name(self) -> str:
        return "supabase"

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


class PostgresBackend(StateBackend):
    SCHEMA_VERSION = "1"

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or resolve_database_url()
        if not self.database_url:
            raise RuntimeError("DATABASE_URL manquant pour le backend PostgreSQL.")

    @property
    def name(self) -> str:
        return "postgres"

    def load(self) -> dict[str, Any]:
        import psycopg
        from psycopg.types.json import Jsonb

        with _lock:
            with psycopg.connect(self.database_url) as conn:
                self._ensure_schema(conn)
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

    def save(self, data: dict[str, Any]) -> None:
        import psycopg
        from psycopg.types.json import Jsonb

        with _lock:
            with psycopg.connect(self.database_url) as conn:
                self._ensure_schema(conn)
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


def load_state() -> dict[str, Any]:
    return get_backend().load()


def save_state(data: dict[str, Any]) -> None:
    get_backend().save(data)


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
