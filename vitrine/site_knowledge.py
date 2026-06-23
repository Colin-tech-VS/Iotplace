"""Build a knowledge snapshot of the public vitrine for the AI advisor."""

from __future__ import annotations

from data import store


def _summarize_startup(s: dict) -> dict:
    return {
        "id": s.get("id"),
        "name": s.get("name"),
        "country": s.get("country"),
        "city": s.get("city"),
        "specialty": s.get("specialty"),
        "skills": (s.get("skills") or [])[:6],
        "rating": s.get("rating"),
        "url_path": f"/startups/{s.get('id')}",
    }


def _summarize_enterprise(e: dict) -> dict:
    return {
        "id": e.get("id"),
        "name": e.get("name"),
        "sector": e.get("sector"),
        "needs": (e.get("needs") or [])[:5],
        "country": e.get("country"),
        "url_path": f"/enterprises/{e.get('id')}",
    }


def _summarize_project(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "title": p.get("title"),
        "enterprise": p.get("enterprise"),
        "status": p.get("status"),
        "budget": p.get("budget"),
        "duration": p.get("duration"),
        "skills": (p.get("skills") or [])[:6],
        "url_path": f"/projects/{p.get('id')}",
    }


def build_site_knowledge(site_url: str = "", locale: str = "en") -> dict:
    site_url = (site_url or store.get_site_url()).rstrip("/")
    pages = []
    for meta in store.get_page_catalog():
        slug = meta["slug"]
        content = store.get_page_content(slug)
        seo = store.get_seo_page(slug)
        entry = {
            "slug": slug,
            "name": meta["name"],
            "path": meta["path"],
            "url": f"{site_url}{meta['path']}",
            "published": content.get("published", True),
        }
        if slug == "home":
            entry["highlights"] = {
                "hero_title": content.get("hero_title"),
                "hero_subtitle": content.get("hero_subtitle"),
            }
        elif slug in ("about", "contact"):
            entry["title"] = content.get("title")
            entry["subtitle"] = content.get("subtitle")
        else:
            entry["title"] = content.get("title")
            entry["subtitle"] = content.get("subtitle")
        entry["seo_description"] = seo.get("description", "")
        pages.append(entry)

    stats = store.get_stats()
    open_projects = [
        p for p in store.get_projects() if p.get("status") in ("Ouvert", "Open")
    ]

    pricing = _build_pricing_knowledge(locale)
    faq_slugs = [meta["slug"] for meta in store.get_page_catalog()]

    return {
        "site_name": "Iotplace",
        "site_url": site_url,
        "tagline": "B2B IoT subcontracting marketplace — enterprises outsource to Asian startups",
        "language": "English",
        "stats": stats,
        "pages": pages,
        "navigation": {
            "home": f"{site_url}/",
            "enterprises": f"{site_url}/enterprises",
            "startups": f"{site_url}/startups",
            "projects": f"{site_url}/projects",
            "about": f"{site_url}/about",
            "contact": f"{site_url}/contact",
            "pricing": f"{site_url}/pricing",
            "register_enterprise": f"{site_url}/inscription/entreprise",
            "register_startup": f"{site_url}/inscription/startup",
            "login": f"{site_url}/connexion",
        },
        "how_it_works": [
            "Enterprises publish IoT subcontracting needs (firmware, hardware, cloud).",
            "Iotplace matches qualified IoT startups in Southeast Asia.",
            "Structured B2B subcontracting with contracts, tracking and secure payments.",
        ],
        "engagement_journey": {
            "phases": ["poc", "scale", "partnership"],
            "summary": "Large enterprises typically progress: quick PoC (3–6 months) → large-scale deployment → long-term partnership if results are good.",
        },
        "startup_countries": store.get_startup_countries(),
        "featured_startups": [_summarize_startup(s) for s in store.get_featured_startups(6)],
        "sample_startups": [_summarize_startup(s) for s in store.get_public_startups()[:12]],
        "partner_enterprises": [_summarize_enterprise(e) for e in store.get_public_enterprises()[:8]],
        "open_projects": [_summarize_project(p) for p in (open_projects or store.get_projects())[:12]],
        "matching_api": f"{site_url}/api/directory/search",
        "pricing": pricing,
        "faq_by_page": {
            slug: store.get_page_faq(slug, locale)[:5]
            for slug in faq_slugs
            if store.get_page_faq(slug, locale)
        },
    }


def _build_pricing_knowledge(locale: str) -> dict:
    """Concise pricing facts so the advisor can answer cost questions precisely."""
    try:
        from payments.pricing_plans import build_pricing_page_context

        pricing = build_pricing_page_context("fr" if locale == "fr" else "en")
    except Exception:
        return {}

    return {
        "commission_percent": pricing.get("commission_percent"),
        "pro_commission_percent": pricing.get("pro_commission_percent"),
        "pro_price_eur": pricing.get("pro_price_eur"),
        "poc_application_fee": pricing.get("poc_application_fee_label"),
        "free_enterprise_max_open_projects": pricing.get("free_enterprise_max_projects"),
        "plans": pricing.get("compare_rows", []),
        "startup_fees": pricing.get("startup_fee_rows", []),
        "notes": (
            "Publier un projet et parcourir l'annuaire est gratuit. Iotplace prélève une "
            "commission par mission livrée ; les paiements passent par un séquestre "
            "(escrow) puis Stripe Connect à la livraison."
            if locale == "fr"
            else
            "Publishing a project and browsing the directory is free. Iotplace charges a "
            "commission per delivered mission; payments go through escrow then Stripe "
            "Connect on delivery."
        ),
    }
