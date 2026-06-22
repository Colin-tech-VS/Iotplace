"""Profile logo upload, media serving, and SIRET/SIREN verification routes."""

from __future__ import annotations

import os

from flask import abort, jsonify, request, send_from_directory

from compte import compte_bp
from compte.api_auth import api_login_required
from compte.profile_helpers import digits_only, user_profile_record
from data import store
from vitrine.i18n import t


@compte_bp.route("/media/logos/<path:relative>")
def serve_profile_logo(relative):
    from compte import profile_media

    if ".." in relative or relative.startswith("/"):
        abort(404)
    root = profile_media._upload_root()
    target = (root / relative.replace("/", os.sep)).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.is_file():
        abort(404)
    return send_from_directory(root, relative.replace("\\", "/"))


@compte_bp.route("/compte/api/profile/logo", methods=["POST"])
@api_login_required()
def upload_profile_logo(user):
    from compte import profile_media

    profile, role, update_fn = user_profile_record(user)
    if not profile:
        return jsonify({"ok": False, "error": "Profil introuvable."}), 404
    file = request.files.get("logo")
    try:
        logo_url = profile_media.save_profile_logo(file, role=role, profile_id=profile["id"])
        profile_media.delete_profile_logo(profile.get("logo_url"))
        update_fn(profile["id"], {"logo_url": logo_url})
        return jsonify({"ok": True, "logo_url": logo_url})
    except profile_media.LogoUploadError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@compte_bp.route("/compte/api/profile/logo/delete", methods=["POST"])
@api_login_required()
def delete_profile_logo(user):
    from compte import profile_media

    profile, _role, update_fn = user_profile_record(user)
    if not profile:
        return jsonify({"ok": False, "error": "Profil introuvable."}), 404
    profile_media.delete_profile_logo(profile.get("logo_url"))
    update_fn(profile["id"], {"logo_url": ""})
    return jsonify({"ok": True})


@compte_bp.route("/compte/api/profile/verify", methods=["POST"])
@api_login_required()
def verify_profile(user):
    from data.company_verification import VerificationError, verify_french_company

    profile, _role, update_fn = user_profile_record(user)
    if not profile:
        return jsonify({"ok": False, "error": "Profil introuvable."}), 404
    payload = request.get_json(silent=True) or {}
    profile_name = (payload.get("profile_name") or profile.get("name") or "").strip()
    siren = payload.get("siren") or profile.get("siren")
    siret = payload.get("siret") or profile.get("siret")
    if not siren and not siret:
        return jsonify({"ok": False, "error": t("compte.profile.verify_missing_id")}), 400
    try:
        result = verify_french_company(
            profile_name=profile_name,
            siren=siren,
            siret=siret,
            use_ai=True,
        )
    except VerificationError as exc:
        update_fn(profile["id"], {
            "verification_status": "failed",
            "verified": False,
            "verification_message": str(exc),
            "verification_ai_summary": "",
        })
        return jsonify({"ok": False, "error": str(exc), "status": "failed"}), 400

    official = result.get("official") or {}
    update_fn(profile["id"], {
        "verification_status": result.get("status"),
        "verified": bool(result.get("verified")),
        "verification_message": result.get("message"),
        "verification_ai_summary": result.get("ai_summary") or "",
        "verification_details": official,
        "verification_checked_at": result.get("checked_at"),
        "legal_name": official.get("legal_name") or profile.get("legal_name"),
        "siren": official.get("siren") or digits_only(siren),
        "siret": official.get("siret") or digits_only(siret),
        "naf_code": official.get("naf_code") or profile.get("naf_code"),
    })
    return jsonify({
        "ok": True,
        "verified": result.get("verified"),
        "status": result.get("status"),
        "message": result.get("message"),
        "ai_summary": result.get("ai_summary"),
        "match_score": result.get("match_score"),
        "official": official,
    })
