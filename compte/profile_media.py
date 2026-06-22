"""Profile logo upload — Supabase Storage or local filesystem."""

from __future__ import annotations

import mimetypes
import os
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage

from data.persistence import DATA_DIR, resolve_supabase_rest_config

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_BYTES = 2 * 1024 * 1024
BUCKET = "profile-logos"


class LogoUploadError(Exception):
    pass


def _upload_root() -> Path:
    custom = (os.environ.get("IOTPLACE_UPLOAD_DIR") or "").strip()
    if custom:
        root = Path(custom)
    else:
        root = DATA_DIR / "uploads"
    logos = root / "logos"
    logos.mkdir(parents=True, exist_ok=True)
    return logos


def _validate_file(file: FileStorage) -> tuple[bytes, str, str]:
    if not file or not file.filename:
        raise LogoUploadError("Aucun fichier sélectionné.")
    data = file.read()
    if not data:
        raise LogoUploadError("Fichier vide.")
    if len(data) > MAX_BYTES:
        raise LogoUploadError("Logo trop volumineux (max 2 Mo).")
    content_type = (file.mimetype or mimetypes.guess_type(file.filename)[0] or "").lower()
    if content_type not in ALLOWED_TYPES:
        raise LogoUploadError("Format non supporté (PNG, JPEG ou WebP uniquement).")
    ext = {".png": "png", ".jpg": "jpg", ".jpeg": "jpg", ".webp": "webp"}.get(
        Path(file.filename).suffix.lower(), "png"
    )
    if "jpeg" in content_type or "jpg" in content_type:
        ext = "jpg"
    elif "webp" in content_type:
        ext = "webp"
    return data, content_type, ext


def _upload_supabase(data: bytes, path: str, content_type: str) -> str:
    from data.persistence import _get_supabase_client

    config = resolve_supabase_rest_config()
    if not config:
        raise LogoUploadError("Supabase non configuré.")
    url, key = config
    client = _get_supabase_client(url, key)
    try:
        client.storage.from_(BUCKET).upload(
            path,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
    except Exception:
        return _upload_local(data, relative)
    public = client.storage.from_(BUCKET).get_public_url(path)
    return public.split("?")[0]


def _upload_local(data: bytes, relative: str) -> str:
    dest = _upload_root() / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return f"/media/logos/{relative.replace(os.sep, '/')}"


def save_profile_logo(file: FileStorage, *, role: str, profile_id: str) -> str:
    data, content_type, ext = _validate_file(file)
    token = uuid.uuid4().hex[:10]
    relative = f"{role}/{profile_id}/logo-{token}.{ext}"
    if resolve_supabase_rest_config():
        return _upload_supabase(data, relative, content_type)
    return _upload_local(data, relative)


def delete_profile_logo(logo_url: str | None) -> None:
    if not logo_url:
        return
    prefix = "/media/logos/"
    if logo_url.startswith(prefix):
        rel = logo_url[len(prefix):]
        path = _upload_root() / rel.replace("/", os.sep)
        if path.is_file():
            path.unlink(missing_ok=True)
