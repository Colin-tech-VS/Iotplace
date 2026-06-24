"""Iotplace vitrine advisor — Mistral-powered site guide."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict

from vitrine.site_knowledge import build_site_knowledge

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
MAX_HISTORY = 12
ADVISOR_RATE_LIMIT = int(os.environ.get("ADVISOR_RATE_LIMIT", "30"))
ADVISOR_RATE_WINDOW = int(os.environ.get("ADVISOR_RATE_WINDOW", "3600"))

_rate_buckets: dict[str, list[float]] = defaultdict(list)

MATCH_INTENT_RE = re.compile(
    r"\b(match|matching|correspond|startup|startups|projet|project|firmware|embedded|"
    r"lorawan|mqtt|skill|compétence|competence|trouver|find|which|quelles?|recommend|"
    r"recommand|cherche|search|annuaire|directory)\b",
    re.I,
)

PROFILE_PROMPTS = {
    "enterprise": (
        "The visitor is an ENTERPRISE (client) looking to outsource IoT work "
        "(firmware, hardware, cloud, integration) to qualified startups."
    ),
    "startup": (
        "The visitor is an IOT STARTUP (subcontractor) in Southeast Asia looking "
        "for missions and projects from large enterprises."
    ),
}

SUGGESTIONS = {
    "en": {
        "enterprise": [
            "How do I publish an IoT project?",
            "Which startups match firmware development?",
            "What does subcontracting on Iotplace cost?",
        ],
        "startup": [
            "How do I find open IoT projects?",
            "How do I apply to a mission?",
            "What skills are most in demand?",
        ],
    },
    "fr": {
        "enterprise": [
            "Comment publier un projet IoT ?",
            "Quelles startups correspondent au développement firmware ?",
            "Combien coûte la sous-traitance sur Iotplace ?",
        ],
        "startup": [
            "Comment trouver des projets IoT ouverts ?",
            "Comment postuler à une mission ?",
            "Quelles compétences sont les plus demandées ?",
        ],
    },
}


class AdvisorError(Exception):
    pass


def is_configured() -> bool:
    return bool((os.environ.get("MISTRAL_API_KEY") or "").strip())


def rate_limit_ok(client_key: str = "global") -> bool:
    from flask import request

    key = client_key
    if request:
        key = f"{client_key}:{request.remote_addr or 'unknown'}"
    now = time.time()
    hits = [stamp for stamp in _rate_buckets[key] if now - stamp < ADVISOR_RATE_WINDOW]
    if len(hits) >= ADVISOR_RATE_LIMIT:
        _rate_buckets[key] = hits
        return False
    hits.append(now)
    _rate_buckets[key] = hits
    return True


def get_suggestions(user_type: str, locale: str = "en") -> list[str]:
    loc = locale if locale in SUGGESTIONS else "en"
    return SUGGESTIONS[loc].get(user_type, SUGGESTIONS[loc]["enterprise"])


def _build_request(messages: list[dict], temperature: float, stream: bool) -> urllib.request.Request:
    api_key = (os.environ.get("MISTRAL_API_KEY") or "").strip()
    if not api_key:
        raise AdvisorError("AI advisor is not configured.")

    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024,
        "stream": stream,
    }
    return urllib.request.Request(
        MISTRAL_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )


def _chat(messages: list[dict], temperature: float = 0.45) -> str:
    request = _build_request(messages, temperature, stream=False)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise AdvisorError(f"AI service error ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise AdvisorError("Cannot reach AI service.") from exc

    choices = body.get("choices") or []
    if not choices:
        raise AdvisorError("Empty AI response.")
    return (choices[0].get("message", {}).get("content") or "").strip()


def _chat_stream(messages: list[dict], temperature: float = 0.45):
    """Yield reply text chunks as the model produces them (Mistral SSE)."""
    request = _build_request(messages, temperature, stream=True)
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as exc:
        raise AdvisorError(f"AI service error ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise AdvisorError("Cannot reach AI service.") from exc

    with response:
        for raw in response:
            line = raw.decode("utf-8", "ignore").strip()
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = (choices[0].get("delta") or {}).get("content")
            if delta:
                yield delta


def _normalize_history(history: list) -> list[dict]:
    cleaned = []
    for item in (history or [])[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content[:2000]})
    return cleaned


def _wants_live_catalog(message: str) -> bool:
    return bool(MATCH_INTENT_RE.search(message or ""))


def _live_catalog_matches(message: str, user_type: str, site_url: str) -> list[dict]:
    from data import store

    site_url = (site_url or store.get_site_url()).rstrip("/")
    query = message.strip()
    search_q = query if len(query) >= 4 else None
    matches: list[dict] = []

    if user_type == "enterprise":
        rows = store.filter_startups_directory(search_q)[:8]
        for row in rows:
            matches.append({
                "type": "startup",
                "name": row.get("name"),
                "url": f"{site_url}/startups/{row.get('id')}",
                "score": row.get("_match_score"),
                "skills": (row.get("skills") or [])[:5],
                "country": row.get("country"),
            })
    else:
        rows = store.filter_projects_directory(search_q)[:8]
        for row in rows:
            if row.get("status") not in ("Ouvert", "Open"):
                continue
            matches.append({
                "type": "project",
                "name": row.get("title"),
                "url": f"{site_url}/projects/{row.get('id')}",
                "score": row.get("_match_score"),
                "enterprise": row.get("enterprise"),
                "skills": (row.get("skills") or [])[:5],
            })
    return matches


def _prepare(user_type, message, history, site_url, locale):
    """Validate input and build (messages, live_matches, user_type) for the LLM."""
    user_type = user_type if user_type in PROFILE_PROMPTS else "enterprise"
    message = (message or "").strip()
    if not message:
        raise AdvisorError("Message is required.")
    if len(message) > 2000:
        raise AdvisorError("Message is too long.")

    lang = "French" if locale == "fr" else "English"
    knowledge = build_site_knowledge(site_url, locale=locale)
    live_matches = _live_catalog_matches(message, user_type, site_url) if _wants_live_catalog(message) else []
    system = _system_prompt(user_type, lang, knowledge, live_matches)

    messages = [{"role": "system", "content": system}]
    messages.extend(_normalize_history(history))
    messages.append({"role": "user", "content": message})
    return messages, live_matches, user_type


def stream(
    user_type: str,
    message: str,
    history: list | None = None,
    site_url: str = "",
    locale: str = "en",
):
    """Generator yielding ('meta', {...}) once, then ('delta', text) chunks."""
    messages, live_matches, user_type = _prepare(user_type, message, history, site_url, locale)
    meta = {
        "suggestions": get_suggestions(user_type, locale),
        "user_type": user_type,
    }
    if live_matches:
        meta["matches"] = live_matches
    yield ("meta", meta)
    for delta in _chat_stream(messages):
        yield ("delta", delta)


def chat(
    user_type: str,
    message: str,
    history: list | None = None,
    site_url: str = "",
    locale: str = "en",
) -> dict:
    messages, live_matches, user_type = _prepare(user_type, message, history, site_url, locale)
    reply = _chat(messages)
    if not reply:
        raise AdvisorError("Empty AI response.")
    result = {
        "reply": reply,
        "suggestions": get_suggestions(user_type, locale),
        "user_type": user_type,
    }
    if live_matches:
        result["matches"] = live_matches
    return result


def _system_prompt(user_type, lang, knowledge, live_matches):
    system = (
        "You are Iota, the official AI assistant of Iotplace — "
        "a B2B IoT subcontracting marketplace connecting global enterprises with "
        "qualified IoT startups in Southeast Asia (Vietnam, Indonesia, Thailand, Philippines).\n"
        "You know the whole Iotplace website: its pages, pricing, how it works, the "
        "engagement journey, startups, enterprises and open projects — all provided in "
        "SITE_KNOWLEDGE below. You are warm, sharp and genuinely helpful, like a great "
        "concierge who already knows the product by heart.\n\n"
        f"{PROFILE_PROMPTS[user_type]}\n\n"
        "Rules:\n"
        f"- Answer in {lang} only.\n"
        "- Use ONLY facts from the SITE_KNOWLEDGE JSON below.\n"
        "- Be concise, friendly and actionable.\n"
        "- Prefer this structure: 1) short direct answer, 2) concrete next steps, "
        "3) relevant page links.\n"
        "- Keep answers practical: mention exact actions and who should do them.\n"
        "- Use **double asterisks** around important words (key actions, page names, "
        "pricing terms, phases like PoC, commission, escrow) — max 3–6 highlights per reply.\n"
        "- Separate paragraphs with a blank line.\n"
        "- Recommend specific site pages using full URLs from navigation when relevant.\n"
        "- If the question is broad, ask ONE short clarifying question at the end.\n"
        "- For signup, point to register_enterprise or register_startup URLs.\n"
        "- When LIVE_MATCHES is provided, cite those real profiles/projects with their URLs.\n"
        "- Do not invent projects, startups or features not in SITE_KNOWLEDGE or LIVE_MATCHES.\n"
        "- If unsure, suggest the contact page.\n\n"
        f"SITE_KNOWLEDGE:\n{json.dumps(knowledge, ensure_ascii=False)}"
    )
    if live_matches:
        system += f"\n\nLIVE_MATCHES:\n{json.dumps(live_matches, ensure_ascii=False)}"
    return system
