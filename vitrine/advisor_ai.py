"""Iotplace vitrine advisor — Mistral-powered site guide."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from vitrine.site_knowledge import build_site_knowledge

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
MAX_HISTORY = 12

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


def get_suggestions(user_type: str, locale: str = "en") -> list[str]:
    loc = locale if locale in SUGGESTIONS else "en"
    return SUGGESTIONS[loc].get(user_type, SUGGESTIONS[loc]["enterprise"])


def _chat(messages: list[dict], temperature: float = 0.45) -> str:
    api_key = (os.environ.get("MISTRAL_API_KEY") or "").strip()
    if not api_key:
        raise AdvisorError("AI advisor is not configured.")

    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024,
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
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AdvisorError(f"AI service error ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise AdvisorError("Cannot reach AI service.") from exc

    choices = body.get("choices") or []
    if not choices:
        raise AdvisorError("Empty AI response.")
    return (choices[0].get("message", {}).get("content") or "").strip()


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


def chat(
    user_type: str,
    message: str,
    history: list | None = None,
    site_url: str = "",
    locale: str = "en",
) -> dict:
    user_type = user_type if user_type in PROFILE_PROMPTS else "enterprise"
    message = (message or "").strip()
    if not message:
        raise AdvisorError("Message is required.")
    if len(message) > 2000:
        raise AdvisorError("Message is too long.")

    lang = "French" if locale == "fr" else "English"
    knowledge = build_site_knowledge(site_url)
    system = (
        "You are Iotplace Copilot, the official AI guide for the Iotplace website — "
        "a B2B IoT subcontracting marketplace connecting global enterprises with "
        "qualified IoT startups in Southeast Asia (Vietnam, Indonesia, Thailand, Philippines).\n\n"
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
        "- Do not invent projects, startups or features not in SITE_KNOWLEDGE.\n"
        "- If unsure, suggest the contact page.\n\n"
        f"SITE_KNOWLEDGE:\n{json.dumps(knowledge, ensure_ascii=False)}"
    )

    messages = [{"role": "system", "content": system}]
    messages.extend(_normalize_history(history))
    messages.append({"role": "user", "content": message})

    reply = _chat(messages)
    if not reply:
        raise AdvisorError("Empty AI response.")

    return {
        "reply": reply,
        "suggestions": get_suggestions(user_type, locale),
        "user_type": user_type,
    }
