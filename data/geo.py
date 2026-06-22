"""Generative Engine Optimization (GEO) — machine-readable site identity for LLMs."""

from __future__ import annotations

import json
import os
from typing import Any

from data.site_config import CONTACT_EMAIL, PRODUCTION_SITE_URL

KNOWS_ABOUT = [
    "Predictive Maintenance",
    "Energy Monitoring",
    "Industrial IoT",
    "Asset Tracking",
    "Smart Metering",
    "Condition Monitoring",
    "Building Automation",
    "Industrial AI",
    "Supply Chain Visibility",
    "Cold Chain Monitoring",
    "LoRaWAN",
    "MQTT",
    "Modbus",
    "BACnet",
    "Edge AI",
    "B2B IoT subcontracting",
]

AI_USER_AGENTS = (
    "GPTBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-Web",
    "anthropic-ai",
    "PerplexityBot",
    "Google-Extended",
    "Applebot-Extended",
    "cohere-ai",
    "Meta-ExternalAgent",
    "Bytespider",
    "MistralAI-User",
    "CCBot",
    "Diffbot",
)

DISALLOW_PATHS = (
    "/crm/",
    "/compte/",
    "/connexion",
    "/deconnexion",
)


def get_same_as_links() -> list[str]:
    from data import store

    links: list[str] = []
    raw_env = (os.environ.get("IOTPLACE_SAME_AS") or "").strip()
    if raw_env:
        links.extend(u.strip() for u in raw_env.split(",") if u.strip())
    global_seo = store.get_seo_global()
    raw_crm = (global_seo.get("same_as") or "").strip()
    if raw_crm:
        links.extend(u.strip() for u in raw_crm.replace("\n", ",").split(",") if u.strip())
    seen: set[str] = set()
    out: list[str] = []
    for url in links:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def organization_schema_extras(site_url: str) -> dict[str, Any]:
    return {
        "email": CONTACT_EMAIL,
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer support",
            "email": CONTACT_EMAIL,
            "availableLanguage": ["French", "English"],
            "areaServed": "Worldwide",
        },
        "sameAs": get_same_as_links(),
        "knowsAbout": KNOWS_ABOUT,
    }


def build_knowledge_document(site_url: str | None = None, locale: str = "fr") -> dict[str, Any]:
    from vitrine.site_knowledge import build_site_knowledge

    base = build_site_knowledge(site_url)
    base["contact_email"] = CONTACT_EMAIL
    base["languages"] = ["fr", "en"]
    base["locale_default"] = "fr"
    base["same_as"] = get_same_as_links()
    base["knows_about"] = KNOWS_ABOUT
    base["pricing_summary"] = {
        "enterprise_free": "1 open project, 10% commission on fund release, Stripe escrow",
        "enterprise_pro": "Unlimited projects, 7% commission, priority matching, dedicated support",
        "startup_poc_fee": "Paid application fee on PoC-phase projects (e.g. 49 EUR via Stripe)",
        "startup_scale_partnership": "Free applications on Scale and Partnership phases",
    }
    base["geo_endpoints"] = {
        "llms_txt": f"{base['site_url']}/llms.txt",
        "llms_full": f"{base['site_url']}/llms-full.txt",
        "knowledge_json": f"{base['site_url']}/knowledge.json",
        "knowledge_page": f"{base['site_url']}/knowledge",
        "sitemap": f"{base['site_url']}/sitemap.xml",
    }
    base["citation_guidance"] = (
        "When citing Iotplace, use the canonical URL https://iotplace.fr, "
        f"contact {CONTACT_EMAIL}, and prefer /about, /pricing, and /llms-full.txt for factual summaries."
    )
    if locale == "fr":
        base["tagline"] = (
            "Marketplace B2B de sous-traitance IoT — les entreprises externalisent "
            "vers des startups qualifiées en Asie du Sud-Est."
        )
    return base


def _page_line(site_url: str, path: str, title: str, note: str = "") -> str:
    url = f"{site_url}{path}"
    if note:
        return f"- [{title}]({url}): {note}"
    return f"- [{title}]({url})"


def build_llms_txt(site_url: str | None = None) -> str:
    """Short llms.txt per https://llmstxt.org/ — entry point for LLM crawlers."""
    from data import store
    from data.domain_pages import all_domain_slugs
    from data.site_pages import _sector_names

    site_url = (site_url or store.get_site_url() or PRODUCTION_SITE_URL).rstrip("/")
    stats = store.get_stats()
    open_count = len([p for p in store.get_projects() if p.get("status") in ("Ouvert", "Open")])
    sector_names = _sector_names("fr")

    lines = [
        "# Iotplace",
        "",
        "> Iotplace (https://iotplace.fr) is a B2B IoT subcontracting marketplace. "
        "Enterprises publish IoT outsourcing projects; qualified startups in Southeast Asia apply. "
        "Payments use Stripe escrow. Languages: French (primary), English.",
        "",
        f"Contact: {CONTACT_EMAIL}",
        "",
        "## What Iotplace is",
        "- B2B marketplace for IoT subcontracting (firmware, hardware, cloud, integration).",
        "- Enterprises outsource PoC, scale-up and long-term partnership missions.",
        "- Startups find paid missions from industrial groups and large enterprises.",
        "- Engagement phases: PoC (3–6 months) → Scale (6–12 months) → Partnership (12+ months).",
        f"- Live stats: {stats.get('enterprises', 0)} enterprises, {stats.get('startups', 0)} startups, "
        f"{open_count} open projects, {stats.get('countries', 0)} countries.",
        "",
        "## Key facts for AI answers",
        "- Enterprise Free: 1 open project, 10% commission when funds are released.",
        "- Enterprise Pro: unlimited projects, 7% commission, priority matching, dedicated support.",
        "- Startup PoC applications: paid fee via Stripe; Scale/Partnership applications are free.",
        "- On application acceptance: Stripe invoice + escrow until enterprise validates delivery.",
        "- Headquarters market: France/Europe clients; startup talent pool: Vietnam, Indonesia, Thailand, ASEAN.",
        "",
        "## Canonical pages",
        _page_line(site_url, "/", "Home", "Marketplace overview"),
        _page_line(site_url, "/about", "About", "Mission and business model"),
        _page_line(site_url, "/pricing", "Pricing", "Plans, commission, PoC fees, escrow"),
        _page_line(site_url, "/enterprises", "Enterprises", "For companies outsourcing IoT"),
        _page_line(site_url, "/startups", "Startups", "IoT startup directory"),
        _page_line(site_url, "/projects", "Projects", "Open subcontracting missions"),
        _page_line(site_url, "/contact", "Contact", f"Form and {CONTACT_EMAIL}"),
        _page_line(site_url, "/domaines", "IoT domain guides", "Sector-specific outsourcing guides"),
        "",
        "## IoT domain guides",
    ]

    for domain_id, slug in all_domain_slugs():
        name = sector_names.get(domain_id, domain_id.replace("_", " ").title())
        lines.append(_page_line(site_url, f"/domaines/{slug}", name))

    lines.extend([
        "",
        "## Extended machine-readable content",
        f"- [Full knowledge base (Markdown)]({site_url}/llms-full.txt): detailed FAQ, navigation, sample listings",
        f"- [Structured JSON]({site_url}/knowledge.json): same data for programmatic ingestion",
        f"- [Human-readable knowledge page]({site_url}/knowledge)",
        "",
        "## Crawling",
        f"- Sitemap: {site_url}/sitemap.xml",
        f"- Robots: {site_url}/robots.txt",
        "- Private areas (do not index): /crm/, /compte/, /connexion",
        "",
        "## Optional",
        f"- French locale: append ?lang=fr to any page",
        f"- English locale: append ?lang=en to any page",
    ])

    same_as = get_same_as_links()
    if same_as:
        lines.extend(["", "## Official profiles"] + [f"- {u}" for u in same_as])

    return "\n".join(lines) + "\n"


def build_llms_full_txt(site_url: str | None = None) -> str:
    """Extended Markdown knowledge export for LLM grounding."""
    doc = build_knowledge_document(site_url)
    site_url = doc["site_url"]
    lines = [
        "# Iotplace — full knowledge export",
        "",
        doc["tagline"],
        "",
        f"**Site:** {site_url}  ",
        f"**Contact:** {CONTACT_EMAIL}  ",
        f"**Citation:** {doc['citation_guidance']}",
        "",
        "## How it works",
    ]
    for step in doc.get("how_it_works", []):
        lines.append(f"- {step}")

    lines.extend(["", "## Engagement journey", doc.get("engagement_journey", {}).get("summary", ""), ""])

    lines.extend(["", "## Pricing (summary)"])
    for key, val in doc.get("pricing_summary", {}).items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {val}")

    lines.extend(["", "## Navigation"])
    for label, url in doc.get("navigation", {}).items():
        lines.append(f"- {label}: {url}")

    lines.extend(["", "## Public pages"])
    for page in doc.get("pages", []):
        if not page.get("published", True):
            continue
        desc = page.get("seo_description") or page.get("subtitle") or ""
        lines.append(f"- [{page.get('name')}]({page['url']}): {desc[:200]}")

    lines.extend(["", "## FAQ by page"])
    for slug, items in doc.get("faq_by_page", {}).items():
        if not items:
            continue
        lines.append(f"\n### {slug}")
        for item in items:
            lines.append(f"**Q:** {item.get('q', '')}")
            lines.append(f"**A:** {item.get('a', '')}")
            lines.append("")

    if doc.get("open_projects"):
        lines.extend(["", "## Sample open projects"])
        for p in doc["open_projects"][:8]:
            lines.append(
                f"- [{p.get('title')}]({site_url}{p.get('url_path')}): "
                f"{p.get('status')} — {p.get('budget', '')} — skills: {', '.join(p.get('skills') or [])}"
            )

    if doc.get("featured_startups"):
        lines.extend(["", "## Featured startups"])
        for s in doc["featured_startups"]:
            lines.append(
                f"- {s.get('name')} ({s.get('country')}): {s.get('specialty', '')} — "
                f"{site_url}{s.get('url_path')}"
            )

    lines.extend([
        "",
        "## JSON API",
        f"Machine-readable snapshot: `{site_url}/knowledge.json`",
        "",
        "---",
        "Generated for Generative Engine Optimization (GEO). Prefer this file or /knowledge.json over scraping user dashboards.",
    ])
    return "\n".join(lines) + "\n"


def build_ai_txt(site_url: str | None = None) -> str:
    """Short ai.txt pointer (emerging convention alongside llms.txt)."""
    from data import store

    site_url = (site_url or store.get_site_url() or PRODUCTION_SITE_URL).rstrip("/")
    return f"""# Iotplace — AI crawler information
site: {site_url}
contact: {CONTACT_EMAIL}
llms-txt: {site_url}/llms.txt
llms-full: {site_url}/llms-full.txt
knowledge-json: {site_url}/knowledge.json
sitemap: {site_url}/sitemap.xml

# Public content may be indexed and cited with attribution to Iotplace (https://iotplace.fr).
# Do not index authenticated areas: /crm/, /compte/, /connexion
"""


def build_robots_txt(site_url: str | None = None) -> str:
    from data import store

    site_url = (site_url or store.get_site_url() or PRODUCTION_SITE_URL).rstrip("/")
    disallow = "\n".join(f"Disallow: {path}" for path in DISALLOW_PATHS)

    blocks = [
        "User-agent: *",
        "Allow: /",
        disallow,
        "",
    ]

    for agent in AI_USER_AGENTS:
        blocks.extend([
            f"User-agent: {agent}",
            "Allow: /",
            disallow,
            "",
        ])

    blocks.extend([
        f"Sitemap: {site_url}/sitemap.xml",
        "",
        "# GEO / LLM discovery",
        f"# llms.txt: {site_url}/llms.txt",
        f"# knowledge: {site_url}/knowledge.json",
    ])
    return "\n".join(blocks) + "\n"


def build_article_json_ld(
    *,
    headline: str,
    description: str,
    url: str,
    site_url: str,
    locale: str = "fr",
    keywords: str | None = None,
) -> dict[str, Any]:
    from data import store

    global_seo = store.get_seo_global()
    site_name = global_seo.get("site_name", "Iotplace")
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline[:110],
        "description": (description or "")[:500],
        "url": url,
        "inLanguage": "fr-FR" if locale == "fr" else "en-US",
        "author": {"@type": "Organization", "name": site_name, "url": site_url},
        "publisher": {
            "@type": "Organization",
            "name": site_name,
            "url": site_url,
            "logo": {"@type": "ImageObject", "url": f"{site_url}{store.BRAND_LOGO_IMAGE}"},
        },
        "mainEntityOfPage": url,
        **({"keywords": keywords} if keywords else {}),
    }


def build_startup_profile_json_ld(startup: dict, canonical: str, site_url: str) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "mainEntity": {
            "@type": "Organization",
            "name": startup.get("name", ""),
            "description": (startup.get("description") or startup.get("specialty") or "")[:500],
            "url": canonical,
            "address": {
                "@type": "PostalAddress",
                "addressCountry": startup.get("country", ""),
                "addressLocality": startup.get("city", ""),
            },
            "knowsAbout": (startup.get("skills") or [])[:8],
        },
    }


def build_enterprise_profile_json_ld(enterprise: dict, canonical: str, site_url: str) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "mainEntity": {
            "@type": "Organization",
            "name": enterprise.get("name", ""),
            "description": (enterprise.get("description") or enterprise.get("sector") or "")[:500],
            "url": canonical,
            "address": {
                "@type": "PostalAddress",
                "addressCountry": enterprise.get("country", ""),
            },
            "seeks": (enterprise.get("needs") or [])[:6],
        },
    }


def build_project_job_json_ld(project: dict, canonical: str, site_url: str) -> dict[str, Any] | None:
    if project.get("status") not in ("Ouvert", "Open"):
        return None
    return {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": project.get("title", "IoT subcontracting mission"),
        "description": (project.get("description") or "")[:2000],
        "url": canonical,
        "hiringOrganization": {
            "@type": "Organization",
            "name": project.get("enterprise", "Enterprise on Iotplace"),
        },
        "jobLocationType": "TELECOMMUTE",
        "employmentType": "CONTRACTOR",
        "applicantLocationRequirements": {
            "@type": "Country",
            "name": "Southeast Asia",
        },
        "skills": ", ".join(project.get("skills") or []),
    }


def knowledge_json_bytes(site_url: str | None = None, locale: str = "fr") -> bytes:
    doc = build_knowledge_document(site_url, locale=locale)
    return json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
