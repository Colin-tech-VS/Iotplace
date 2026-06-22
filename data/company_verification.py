"""French company verification via the official Annuaire des Entreprises API."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

API_BASE = "https://recherche-entreprises.api.gouv.fr"
USER_AGENT = "Iotplace/1.0 (profile-verification; contact@iotplace.fr)"


class VerificationError(Exception):
    pass


def normalize_digits(value: str | None, length: int) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != length:
        raise VerificationError(f"Numéro invalide : {length} chiffres attendus.")
    return digits


def normalize_siren(value: str | None) -> str:
    return normalize_digits(value, 9)


def normalize_siret(value: str | None) -> str:
    return normalize_digits(value, 14)


def _normalize_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", (name or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    for token in ("sas", "sarl", "sa", "eurl", "sci", "sca", "scop", "groupe", "group"):
        text = re.sub(rf"\b{token}\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def name_similarity(a: str, b: str) -> float:
    na, nb = _normalize_name(a), _normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb or na in nb or nb in na:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def _http_get_json(url: str) -> dict[str, Any]:
    req = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise VerificationError("Établissement introuvable dans le registre officiel.") from exc
        raise VerificationError(f"Registre officiel indisponible (HTTP {exc.code}).") from exc
    except URLError as exc:
        raise VerificationError("Impossible de joindre le registre officiel des entreprises.") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError("Réponse invalide du registre officiel.") from exc


def fetch_establishment(siret: str) -> dict[str, Any]:
    data = _http_get_json(f"{API_BASE}/search?q={siret}&per_page=5")
    results = data.get("results") or []
    for item in results:
        siege = item.get("siege") or {}
        if normalize_digits(siege.get("siret", ""), 14) == siret:
            return item
        for etab in item.get("matching_etablissements") or []:
            if normalize_digits(etab.get("siret", ""), 14) == siret:
                return {**item, "matched_etablissement": etab}
    if results and normalize_digits((results[0].get("siege") or {}).get("siret", ""), 14) == siret:
        return results[0]
    raise VerificationError("SIRET introuvable dans le registre officiel.")


def fetch_company_by_siren(siren: str) -> dict[str, Any]:
    data = _http_get_json(f"{API_BASE}/search?q={siren}&per_page=1")
    results = data.get("results") or []
    if not results:
        raise VerificationError("SIREN introuvable dans le registre officiel.")
    match = results[0]
    if normalize_digits(match.get("siren", ""), 9) != siren:
        raise VerificationError("SIREN introuvable dans le registre officiel.")
    return match


def _extract_official_fields(payload: dict[str, Any], *, from_siret: bool) -> dict[str, Any]:
    if from_siret:
        matched = payload.get("matched_etablissement")
        siege = payload.get("siege") or {}
        etab = matched or siege
        unite = payload
        official_name = (
            etab.get("nom_commercial")
            or payload.get("nom_complet")
            or payload.get("denomination")
            or payload.get("nom_raison_sociale")
            or ""
        )
        siren = normalize_digits(payload.get("siren", ""), 9)
        siret = normalize_digits(etab.get("siret", ""), 14)
        address = etab.get("adresse") or siege.get("adresse") or ""
        return {
            "official_name": official_name.strip(),
            "legal_name": (payload.get("denomination") or payload.get("nom_raison_sociale") or official_name).strip(),
            "siren": siren,
            "siret": siret,
            "naf_code": etab.get("activite_principale") or payload.get("activite_principale") or "",
            "naf_label": payload.get("libelle_activite_principale") or "",
            "address": address.strip(),
            "city": etab.get("libelle_commune") or siege.get("libelle_commune") or "",
            "postal_code": etab.get("code_postal") or siege.get("code_postal") or "",
            "is_active": etab.get("etat_administratif") in (None, "A", "Actif"),
            "source": "recherche-entreprises.api.gouv.fr",
        }

    official_name = (
        payload.get("nom_complet")
        or payload.get("nom_raison_sociale")
        or payload.get("denomination")
        or ""
    )
    siege = payload.get("siege") or {}
    return {
        "official_name": official_name.strip(),
        "legal_name": (payload.get("denomination") or payload.get("nom_raison_sociale") or official_name).strip(),
        "siren": normalize_digits(payload.get("siren", ""), 9),
        "siret": normalize_digits(siege.get("siret", ""), 14) if siege.get("siret") else "",
        "naf_code": payload.get("activite_principale") or siege.get("activite_principale") or "",
        "naf_label": payload.get("libelle_activite_principale") or "",
        "address": siege.get("adresse") or "",
        "city": siege.get("libelle_commune") or "",
        "postal_code": siege.get("code_postal") or "",
        "is_active": payload.get("etat_administratif") in (None, "A", "Actif"),
        "source": "recherche-entreprises.api.gouv.fr",
    }


def _ai_verification_summary(profile_name: str, official: dict[str, Any], score: float) -> str | None:
    api_key = (__import__("os").environ.get("MISTRAL_API_KEY") or "").strip()
    if not api_key:
        return None
    prompt = (
        "Tu es un vérificateur KYC B2B. Compare le nom de profil marketplace avec les données INSEE.\n"
        f"Profil: {profile_name}\n"
        f"Officiel: {official.get('legal_name')} / {official.get('official_name')}\n"
        f"SIREN: {official.get('siren')} SIRET: {official.get('siret')}\n"
        f"Adresse: {official.get('address')}\n"
        f"Score similarité automatique: {score:.0%}\n"
        "Réponds en 2 phrases max en français : correspondance ou écart, sans inventer."
    )
    payload = {
        "model": __import__("os").environ.get("MISTRAL_MODEL", "mistral-small-latest"),
        "messages": [
            {"role": "system", "content": "Analyse factuelle de correspondance entreprise. Pas d'invention."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 180,
    }
    try:
        req = Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return (body.get("choices") or [{}])[0].get("message", {}).get("content", "").strip() or None
    except Exception:
        return None


def verify_french_company(
    *,
    profile_name: str,
    siren: str | None = None,
    siret: str | None = None,
    use_ai: bool = True,
) -> dict[str, Any]:
    profile_name = (profile_name or "").strip()
    if not profile_name:
        raise VerificationError("Nom de l'entreprise requis pour la vérification.")

    siret_norm = normalize_siret(siret) if siret else None
    siren_norm = normalize_siren(siren) if siren else None
    if siret_norm and not siren_norm:
        siren_norm = siret_norm[:9]
    if siren_norm and siret_norm and siret_norm[:9] != siren_norm:
        raise VerificationError("Le SIRET ne correspond pas au SIREN saisi.")

    if siret_norm:
        payload = fetch_establishment(siret_norm)
        official = _extract_official_fields(payload, from_siret=True)
    elif siren_norm:
        payload = fetch_company_by_siren(siren_norm)
        official = _extract_official_fields(payload, from_siret=False)
    else:
        raise VerificationError("Saisissez un numéro SIREN ou SIRET.")

    if not official.get("is_active", True):
        raise VerificationError("L'établissement n'est plus actif au registre officiel.")

    score = max(
        name_similarity(profile_name, official.get("official_name", "")),
        name_similarity(profile_name, official.get("legal_name", "")),
    )
    verified = score >= 0.72
    ai_summary = _ai_verification_summary(profile_name, official, score) if use_ai else None

    if not verified and ai_summary:
        low = ai_summary.lower()
        if any(w in low for w in ("correspond", "identique", "cohérent", "valid")):
            if "ne correspond" not in low and "pas correspond" not in low:
                verified = score >= 0.55

    status = "verified" if verified else "failed"
    message = (
        "Profil vérifié — correspondance avec le registre officiel."
        if verified
        else "Correspondance insuffisante entre le nom du profil et le registre officiel."
    )

    return {
        "ok": verified,
        "status": status,
        "verified": verified,
        "message": message,
        "match_score": round(score, 3),
        "official": official,
        "ai_summary": ai_summary,
        "checked_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
