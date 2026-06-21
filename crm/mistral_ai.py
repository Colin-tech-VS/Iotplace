"""Mistral AI content generation for vitrine pages."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

PAGE_FIELDS = {
    "home": [
        "hero_badge",
        "hero_title",
        "hero_highlight",
        "hero_subtitle",
        "cta_primary",
        "cta_secondary",
    ],
    "about": ["title", "subtitle", "mission_1", "mission_2"],
    "contact": ["title", "subtitle", "email"],
}

DEFAULT_FIELDS = ["title", "subtitle"]


class MistralError(Exception):
    pass


def is_configured() -> bool:
    return bool((os.environ.get("MISTRAL_API_KEY") or "").strip())


def _fields_for_slug(slug: str) -> list[str]:
    return PAGE_FIELDS.get(slug, DEFAULT_FIELDS)


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise MistralError("Empty response from Mistral.")
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise MistralError("Mistral returned invalid JSON.") from exc


def _chat(messages: list[dict], temperature: float = 0.65) -> str:
    api_key = (os.environ.get("MISTRAL_API_KEY") or "").strip()
    if not api_key:
        raise MistralError("MISTRAL_API_KEY is not configured.")

    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        MISTRAL_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise MistralError(f"Mistral API error ({exc.code}): {detail[:240]}") from exc
    except urllib.error.URLError as exc:
        raise MistralError(f"Cannot reach Mistral API: {exc.reason}") from exc

    choices = body.get("choices") or []
    if not choices:
        raise MistralError("Mistral returned no content.")
    return choices[0].get("message", {}).get("content", "")


def _normalize_content(slug: str, raw: dict) -> dict:
    fields = _fields_for_slug(slug)
    content = {}
    for field in fields:
        value = raw.get(field, "")
        content[field] = str(value).strip() if value is not None else ""
    return content


def _normalize_seo(raw: dict) -> dict:
    return {
        "title": str(raw.get("title", "")).strip()[:120],
        "description": str(raw.get("description", "")).strip()[:320],
        "keywords": str(raw.get("keywords", "")).strip()[:500],
    }


def _normalize_faq(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    items = []
    for entry in raw[:6]:
        if not isinstance(entry, dict):
            continue
        question = str(entry.get("q", "")).strip()
        answer = str(entry.get("a", "")).strip()
        if question and answer:
            items.append({"q": question, "a": answer})
    return items


def generate_page_content(
    slug: str,
    page_name: str,
    page_path: str,
    user_prompt: str = "",
    current_content: dict | None = None,
    include_seo: bool = True,
    include_faq: bool = True,
) -> dict:
    fields = _fields_for_slug(slug)
    current_content = current_content or {}
    extra = (user_prompt or "").strip()

    system = (
        "You are a B2B copywriter for Iotplace, an IoT subcontracting marketplace connecting "
        "global enterprises with qualified IoT startups in Southeast Asia (Vietnam, Indonesia, Thailand). "
        "Write in English only. Be professional, concise and SEO-friendly. "
        "Return a single valid JSON object with no markdown."
    )

    user = {
        "task": "Generate website page copy for Iotplace vitrine.",
        "page_slug": slug,
        "page_name": page_name,
        "page_path": page_path,
        "content_fields": fields,
        "include_seo": include_seo,
        "include_faq": include_faq,
        "current_content": {k: current_content.get(k, "") for k in fields},
        "editor_instructions": extra or "Write fresh, compelling copy tailored to this page.",
        "output_schema": {
            "content": {field: "string" for field in fields},
            "seo": {
                "title": "string (max 60 chars)",
                "description": "string (max 160 chars)",
                "keywords": "comma-separated string",
            }
            if include_seo
            else None,
            "faq": [{"q": "question", "a": "answer"}] if include_faq else None,
        },
    }

    raw_text = _chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ]
    )
    parsed = _extract_json(raw_text)

    result = {
        "content": _normalize_content(slug, parsed.get("content") or parsed),
        "seo": _normalize_seo(parsed.get("seo") or {}) if include_seo else {},
        "faq": _normalize_faq(parsed.get("faq") or []) if include_faq else [],
    }
    return result
