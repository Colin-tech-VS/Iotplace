from flask import flash, jsonify, redirect, render_template, request, session, url_for

import auth
from compte import compte_bp
from compte.api_auth import api_login_required
from data import store
from payments import handlers as payment_handlers
from payments import poc_application
from payments import stripe_service

from vitrine.i18n import t
from vitrine.sectors import parse_sector_fields


def _process_application_status(message_id, user, status):
    updated = store.update_message_status(message_id, user["id"], status)
    if not updated:
        return None, None
    payment_result = None
    if status == "accepted" and updated.get("kind") == "application":
        payment_result = payment_handlers.on_application_accepted(updated, user)
    return updated, payment_result


def _validate_credentials(email, password, password_confirm=None, check_exists=True):
    errors = []
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        errors.append(t("compte.error_invalid_email", default="Invalid email."))
    if not password or len(password) < 8:
        errors.append(t("compte.error_password_short", default="Password must be at least 8 characters."))
    if password_confirm is not None and password != password_confirm:
        errors.append(t("compte.error_password_mismatch", default="Passwords do not match."))
    if check_exists and email and store.email_exists(email):
        errors.append(t("compte.error_email_exists", default="An account already exists with this email."))
    return errors


def _enterprise_account_context(user, profile, active_page="dashboard"):
    from payments import subscriptions
    from payments.pricing_plans import build_pricing_page_context, is_pro_enterprise
    from vitrine.i18n import get_locale

    profile = subscriptions.sync_enterprise_subscription(profile) or profile
    dash = store.get_dashboard_data_for_enterprise(user, profile)
    pricing = build_pricing_page_context(get_locale())
    return {
        "user": user,
        "profile": profile,
        "active_page": active_page,
        "stripe_configured": stripe_service.is_configured(),
        "is_pro": is_pro_enterprise(profile),
        "pricing": pricing,
        **dash,
    }


def _startup_account_context(user, profile, active_page="dashboard"):
    from payments.pricing_plans import build_pricing_page_context
    from vitrine.i18n import get_locale

    dash = store.get_dashboard_data_for_startup(user, profile)
    pricing = build_pricing_page_context(get_locale())
    return {
        "user": user,
        "profile": profile,
        "active_page": active_page,
        "stripe_configured": stripe_service.is_configured(),
        "pricing": pricing,
        **dash,
    }


@compte_bp.route("/connexion", methods=["GET", "POST"])
def login():
    if auth.get_current_user():
        return redirect(url_for("compte.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = store.get_user_by_email(email)
        if user and auth.verify_password(user["password_hash"], password):
            auth.login_user(user)
            flash(t("compte.flash_login_ok"), "success")
            next_url = request.args.get("next") or url_for("compte.home")
            return redirect(next_url)
        flash(t("compte.flash_login_fail"), "error")

    return render_template("compte/login.html")


@compte_bp.route("/connexion/mot-de-passe-oublie", methods=["GET", "POST"])
def forgot_password():
    from compte import mailer
    from vitrine.i18n import get_locale

    if auth.get_current_user():
        return redirect(url_for("compte.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        locale = get_locale()
        token, user = store.issue_password_reset_token(email)
        if token and user:
            reset_url = store.get_site_url().rstrip("/") + url_for("compte.reset_password", token=token)
            try:
                mailer.send_password_reset_email(user["email"], reset_url, locale=locale)
            except mailer.MailDeliveryError:
                flash(t("compte.flash_reset_email_error"), "error")
                return render_template("compte/forgot_password.html", form={"email": email})
        flash(t("compte.flash_reset_email_sent"), "success")
        return redirect(url_for("compte.login"))

    return render_template("compte/forgot_password.html", form={})


@compte_bp.route("/connexion/reinitialiser/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = store.get_user_by_password_reset_token(token)
    if not user:
        flash(t("compte.flash_reset_link_invalid"), "error")
        return redirect(url_for("compte.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        errors = _validate_credentials(user["email"], password, password_confirm, check_exists=False)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("compte/reset_password.html", token=token)
        store.update_user_password(user["id"], auth.hash_password(password))
        flash(t("compte.flash_reset_ok"), "success")
        return redirect(url_for("compte.login"))

    return render_template("compte/reset_password.html", token=token)


@compte_bp.route("/deconnexion")
def logout():
    auth.logout_user()
    flash(t("compte.flash_logout"), "success")
    return redirect(url_for("vitrine.index"))


@compte_bp.route("/compte")
def home():
    user = auth.get_current_user()
    if not user:
        return redirect(url_for("compte.login"))
    if user["role"] == "enterprise":
        return redirect(url_for("compte.enterprise_dashboard"))
    return redirect(url_for("compte.startup_dashboard"))


def _registration_form():
    if request.method == "POST":
        return dict(request.form)
    form = {}
    preselect = (request.args.get("sector_id") or request.args.get("domain") or "").strip()
    if preselect:
        form["sector_id"] = preselect
    return form


@compte_bp.route("/inscription/entreprise", methods=["GET", "POST"])
def register_enterprise():
    if auth.get_current_user():
        return redirect(url_for("compte.home"))

    if request.method == "POST":
        errors = _validate_credentials(
            request.form.get("email"),
            request.form.get("password"),
            request.form.get("password_confirm"),
        )
        if not request.form.get("company_name", "").strip():
            errors.append(t("compte.error_company_name_required"))
        if not request.form.get("contact_name", "").strip():
            errors.append(t("compte.error_contact_name_required"))
        sector_fields = parse_sector_fields(request.form, t)
        if not sector_fields.get("sector_id"):
            errors.append(t("compte.error_sector_required", default="Veuillez sélectionner un domaine IoT."))

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("compte/register_enterprise.html", form=dict(request.form))

        try:
            project_fields = None
            project_need = request.form.get("project_need", "").strip()
            if project_need:
                project_fields = {
                    "title": project_need[:120],
                    "description": project_need,
                    "budget": "",
                    "duration": "",
                    "skills": [],
                    "engagement_phase": "poc",
                }

            user, _profile = store.register_enterprise_account(
                {
                    "email": request.form.get("email", "").strip().lower(),
                    "password_hash": auth.hash_password(request.form.get("password", "")),
                },
                {
                    "name": request.form.get("company_name", "").strip(),
                    **sector_fields,
                    "contact_name": request.form.get("contact_name", "").strip(),
                    "email": request.form.get("email", "").strip().lower(),
                },
                project_fields,
            )
            auth.login_user(user)
            store.track_signup_conversion("enterprise", session.get("analytics_sid"))
            flash(t("compte.flash_register_ent_ok"), "success")
            if request.args.get("plan") == "pro" or request.form.get("plan") == "pro":
                return redirect(url_for("compte.enterprise_subscribe_pro"))
            return redirect(url_for("compte.enterprise_dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("compte/register_enterprise.html", form=_registration_form())

    return render_template("compte/register_enterprise.html", form=_registration_form())


@compte_bp.route("/inscription/startup", methods=["GET", "POST"])
def register_startup():
    if auth.get_current_user():
        return redirect(url_for("compte.home"))

    if request.method == "POST":
        errors = _validate_credentials(
            request.form.get("email"),
            request.form.get("password"),
            request.form.get("password_confirm"),
        )
        if not request.form.get("startup_name", "").strip():
            errors.append(t("compte.error_startup_name_required"))
        if not request.form.get("country", "").strip():
            errors.append(t("compte.error_country_required"))
        sector_fields = parse_sector_fields(request.form, t)
        if not sector_fields.get("sector_id"):
            errors.append(t("compte.error_sector_required", default="Veuillez sélectionner un domaine IoT."))

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("compte/register_startup.html", form=dict(request.form))

        try:
            sector_label = sector_fields.get("sector") or ""
            user, _profile = store.register_startup_account(
                {
                    "email": request.form.get("email", "").strip().lower(),
                    "password_hash": auth.hash_password(request.form.get("password", "")),
                },
                {
                    "name": request.form.get("startup_name", "").strip(),
                    **sector_fields,
                    "country": request.form.get("country", "").strip(),
                    "specialty": sector_label,
                    "skills": [sector_label] if sector_label else [],
                },
            )
            auth.login_user(user)
            store.track_signup_conversion("startup", session.get("analytics_sid"))
            flash(t("compte.flash_register_st_ok"), "success")
            return redirect(url_for("compte.startup_dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("compte/register_startup.html", form=_registration_form())

    return render_template("compte/register_startup.html", form=_registration_form())


@compte_bp.route("/compte/entreprise")
@auth.login_required(role="enterprise")
def enterprise_dashboard():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_ent_missing"), "error")
        return redirect(url_for("vitrine.index"))
    from payments import subscriptions
    from payments.pricing_plans import get_pricing_numbers, is_pro_enterprise

    profile = subscriptions.sync_enterprise_subscription(profile) or profile
    if request.args.get("billing") == "cancel":
        flash(t("compte.flash_pro_incomplete"), "info")
    dash = store.get_dashboard_data_for_enterprise(user, profile)
    pricing = get_pricing_numbers()
    return render_template(
        "compte/dashboard_enterprise.html",
        user=user,
        profile=profile,
        stripe_configured=stripe_service.is_configured(),
        is_pro=is_pro_enterprise(profile),
        pricing=pricing,
        **dash,
    )


@compte_bp.route("/compte/entreprise/projet/nouveau", methods=["GET", "POST"])
@auth.login_required(role="enterprise")
def enterprise_new_project():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    if not profile:
        return redirect(url_for("vitrine.index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash(t("compte.flash_project_title_required"), "error")
            return render_template("compte/project_form.html", profile=profile, user=user, form=dict(request.form))
        allowed, limit_msg = store.can_enterprise_add_open_project(profile)
        if not allowed:
            flash(limit_msg, "warning")
            return render_template("compte/project_form.html", profile=profile, user=user, form=dict(request.form))
        try:
            store.add_project_for_enterprise(profile, {
                "title": title,
                "description": request.form.get("description", "").strip(),
                "budget": request.form.get("budget", "").strip(),
                "duration": request.form.get("duration", "").strip(),
                "skills": store.parse_list_field(request.form.get("skills")),
                "status": "Ouvert",
                "engagement_phase": request.form.get("engagement_phase", "").strip(),
            })
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("compte/project_form.html", profile=profile, user=user, form=dict(request.form))
        flash(t("compte.flash_project_published"), "success")
        return redirect(url_for("compte.enterprise_dashboard"))

    return render_template("compte/project_form.html", profile=profile, user=user, form={})


@compte_bp.route("/compte/entreprise/projet/<project_id>/modifier", methods=["GET", "POST"])
@auth.login_required(role="enterprise")
def enterprise_edit_project(project_id):
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project or project.get("enterprise_id") != profile["id"]:
        flash(t("compte.flash_project_not_found"), "error")
        return redirect(url_for("compte.enterprise_dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash(t("compte.flash_project_title_required"), "error")
            return render_template(
                "compte/project_form.html",
                profile=profile,
                user=user,
                project=project,
                form=dict(request.form),
            )
        new_status = request.form.get("status", "").strip()
        if new_status == "Ouvert" and project.get("status") != "Ouvert":
            allowed, limit_msg = store.can_enterprise_add_open_project(profile)
            if not allowed:
                flash(limit_msg, "warning")
                return render_template(
                    "compte/project_form.html",
                    profile=profile,
                    user=user,
                    project=project,
                    form=dict(request.form),
                )
        store.update_project_for_enterprise(profile, project_id, {
            "title": title,
            "description": request.form.get("description", "").strip(),
            "budget": request.form.get("budget", "").strip(),
            "duration": request.form.get("duration", "").strip(),
            "skills": store.parse_list_field(request.form.get("skills")),
            "status": new_status,
            "engagement_phase": request.form.get("engagement_phase", "").strip(),
        })
        flash(t("compte.flash_project_updated"), "success")
        return redirect(url_for("compte.enterprise_project_detail", project_id=project_id))

    form = {
        "title": project.get("title", ""),
        "description": project.get("description", ""),
        "budget": project.get("budget", ""),
        "duration": project.get("duration", ""),
        "skills": ", ".join(project.get("skills") or []),
        "status": project.get("status", "Ouvert"),
        "engagement_phase": project.get("engagement_phase", ""),
    }
    return render_template(
        "compte/project_form.html",
        profile=profile,
        user=user,
        project=project,
        form=form,
    )


@compte_bp.route("/compte/entreprise/projet/<project_id>")
@auth.login_required(role="enterprise")
def enterprise_project_detail(project_id):
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project or project.get("enterprise_id") != profile["id"]:
        flash(t("compte.flash_project_not_found"), "error")
        return redirect(url_for("compte.enterprise_dashboard"))
    applications = [
        store.enrich_message_for_view(a, user["id"])
        for a in store.get_applications_for_project(project_id)
    ]
    return render_template(
        "compte/project_detail.html",
        user=user,
        profile=profile,
        project=project,
        applications=applications,
        role="enterprise",
    )


@compte_bp.route("/compte/entreprise/profil", methods=["GET", "POST"])
@auth.login_required(role="enterprise")
def enterprise_edit_profile():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_ent_missing"), "error")
        return redirect(url_for("vitrine.index"))

    if request.method == "POST":
        sector_fields = parse_sector_fields(request.form, t)
        store.update_enterprise_profile(profile["id"], {
            "name": request.form.get("company_name", "").strip(),
            **sector_fields,
            "country": request.form.get("country", "").strip(),
            "city": request.form.get("city", "").strip(),
            "company_size": request.form.get("company_size", "").strip(),
            "contact_name": request.form.get("contact_name", "").strip(),
            "contact_role": request.form.get("contact_role", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "website": request.form.get("website", "").strip(),
            "description": request.form.get("description", "").strip(),
            "besoin": request.form.get("besoin", "").strip(),
            "needs": store.parse_list_field(request.form.get("needs")),
        })
        flash(t("compte.flash_profile_updated"), "success")
        return redirect(url_for("compte.enterprise_edit_profile"))

    return render_template(
        "compte/edit_enterprise.html",
        **_enterprise_account_context(user, profile, active_page="profile"),
        form={
            "sector_id": profile.get("sector_id", ""),
            "sector_other": profile.get("sector_other", ""),
            "sector": profile.get("sector", ""),
        },
    )


@compte_bp.route("/compte/entreprise/offres")
@auth.login_required(role="enterprise")
def enterprise_pricing():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_ent_missing"), "error")
        return redirect(url_for("vitrine.index"))
    return render_template(
        "compte/pricing_enterprise.html",
        **_enterprise_account_context(user, profile, active_page="pricing"),
    )


@compte_bp.route("/compte/startup")
@auth.login_required(role="startup")
def startup_dashboard():
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_st_missing"), "error")
        return redirect(url_for("vitrine.index"))
    dash = store.get_dashboard_data_for_startup(user, profile)
    return render_template(
        "compte/dashboard_startup.html",
        user=user,
        profile=profile,
        stripe_configured=stripe_service.is_configured(),
        **dash,
    )


@compte_bp.route("/compte/startup/projet/<project_id>")
@auth.login_required(role="startup")
def startup_project_detail(project_id):
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project:
        flash(t("compte.flash_project_not_found"), "error")
        return redirect(url_for("compte.startup_dashboard"))
    application = next(
        (store.enrich_message_for_view(a, user["id"]) for a in store.get_applications_for_startup(profile["id"])
         if a.get("project_id") == project_id),
        None,
    )
    return render_template(
        "compte/project_detail.html",
        user=user,
        profile=profile,
        project=project,
        applications=[application] if application else [],
        role="startup",
        already_applied=store.startup_already_applied(profile["id"], project_id),
        requires_poc_fee=poc_application.project_requires_poc_fee(project),
        poc_application_fee_label=stripe_service.format_poc_application_fee(),
        stripe_configured=stripe_service.is_configured(),
    )


@compte_bp.route("/compte/startup/projet/<project_id>/postuler", methods=["POST"])
@auth.login_required(role="startup")
def startup_apply_project(project_id):
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project:
        flash(t("compte.flash_project_not_found"), "error")
        return redirect(url_for("compte.startup_dashboard"))
    body = request.form.get("message", "").strip()
    if not body:
        flash(t("compte.flash_apply_message_required"), "error")
        return redirect(url_for("compte.startup_project_detail", project_id=project_id))

    if poc_application.project_requires_poc_fee(project):
        if not stripe_service.is_configured():
            flash(t("compte.flash_poc_stripe_missing"), "error")
            return redirect(url_for("compte.startup_project_detail", project_id=project_id))
        try:
            result = poc_application.start_poc_application(user, profile, project, body)
            return redirect(result["checkout_url"])
        except ValueError as exc:
            flash(str(exc), "error")
        except stripe_service.PaymentError as exc:
            flash(str(exc), "error")
        return redirect(url_for("compte.startup_project_detail", project_id=project_id))

    try:
        store.apply_to_project(user, profile, project, body)
        flash(t("compte.flash_apply_sent"), "success")
        return redirect(url_for("compte.startup_dashboard") + "#messages")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("compte.startup_project_detail", project_id=project_id))


@compte_bp.route("/compte/startup/projet/<project_id>/candidature/succes")
@auth.login_required(role="startup")
def startup_apply_poc_success(project_id):
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project:
        flash(t("compte.flash_project_not_found"), "error")
        return redirect(url_for("compte.startup_dashboard"))

    session_id = (request.args.get("session_id") or "").strip()
    result = poc_application.complete_from_session_id(session_id)
    if result.get("ok"):
        flash(t("compte.flash_poc_apply_ok"), "success")
        return redirect(url_for("compte.startup_dashboard") + "#messages")

    flash(result.get("error", t("compte.flash_payment_pending")), "warning")
    return redirect(url_for("compte.startup_project_detail", project_id=project_id))


@compte_bp.route("/compte/startup/profil", methods=["GET", "POST"])
@auth.login_required(role="startup")
def startup_edit_profile():
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_st_missing"), "error")
        return redirect(url_for("vitrine.index"))

    if request.method == "POST":
        sector_fields = parse_sector_fields(request.form, t)
        store.update_startup_profile(profile["id"], {
            "name": request.form.get("startup_name", "").strip(),
            **sector_fields,
            "country": request.form.get("country", "").strip(),
            "flag": request.form.get("flag", "").strip(),
            "city": request.form.get("city", "").strip(),
            "contact_name": request.form.get("contact_name", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "specialty": request.form.get("specialty", "").strip(),
            "team_size": int(request.form.get("team_size") or 0),
            "projects_done": int(request.form.get("projects_done") or 0),
            "availability": request.form.get("availability", "").strip(),
            "rate_range": request.form.get("rate_range", "").strip(),
            "description": request.form.get("description", "").strip(),
            "besoin": request.form.get("besoin", "").strip(),
            "skills": store.parse_list_field(request.form.get("skills")),
        })
        flash(t("compte.flash_profile_updated"), "success")
        return redirect(url_for("compte.startup_edit_profile"))

    return render_template(
        "compte/edit_startup.html",
        **_startup_account_context(user, profile, active_page="profile"),
        form={
            "sector_id": profile.get("sector_id", ""),
            "sector_other": profile.get("sector_other", ""),
            "sector": profile.get("sector", ""),
        },
    )


@compte_bp.route("/compte/startup/offres")
@auth.login_required(role="startup")
def startup_pricing():
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_st_missing"), "error")
        return redirect(url_for("vitrine.index"))
    return render_template(
        "compte/pricing_startup.html",
        **_startup_account_context(user, profile, active_page="pricing"),
    )


@compte_bp.route("/compte/messages/<message_id>")
@auth.login_required()
def message_detail(message_id):
    user = auth.get_current_user()
    msg = store.get_message(message_id)
    if not msg or user["id"] not in (msg.get("from_user_id"), msg.get("to_user_id")):
        flash(t("compte.flash_message_not_found"), "error")
        return redirect(url_for("compte.home"))
    if msg.get("to_user_id") == user["id"] and not msg.get("read"):
        store.mark_message_read(message_id, user["id"])
    enriched = store.enrich_message_for_view(msg, user["id"])
    project = store.get_project(msg["project_id"]) if msg.get("project_id") else None
    engagement = store.get_engagement_by_message(message_id) if msg.get("kind") == "application" else None
    engagement_label = store.format_engagement_label(engagement["status"]) if engagement else None
    return render_template(
        "compte/message_detail.html",
        user=user,
        message=enriched,
        project=project,
        engagement=engagement,
        engagement_label=engagement_label,
        stripe_configured=stripe_service.is_configured(),
    )


@compte_bp.route("/compte/messages/<message_id>/repondre", methods=["POST"])
@auth.login_required()
def message_reply(message_id):
    user = auth.get_current_user()
    original = store.get_message(message_id)
    if not original or user["id"] not in (original.get("from_user_id"), original.get("to_user_id")):
        flash(t("compte.flash_message_not_found"), "error")
        return redirect(url_for("compte.home"))
    body = request.form.get("body", "").strip()
    if not body:
        flash(t("compte.flash_message_empty"), "error")
        return redirect(url_for("compte.message_detail", message_id=message_id))
    recipient_id = (
        original["from_user_id"]
        if original.get("to_user_id") == user["id"]
        else original["to_user_id"]
    )
    recipient = store.get_user(recipient_id)
    if not recipient:
        flash(t("compte.flash_recipient_not_found"), "error")
        return redirect(url_for("compte.message_detail", message_id=message_id))
    project = store.get_project(original["project_id"]) if original.get("project_id") else None
    subject = f"Re: {original.get('subject', 'Message')}"
    store.send_message(user, recipient, subject, body, kind="reply", project=project)
    flash(t("compte.flash_reply_sent"), "success")
    return redirect(url_for("compte.message_detail", message_id=message_id))


@compte_bp.route("/compte/messages/<message_id>/statut", methods=["POST"])
@auth.login_required(role="enterprise")
def message_update_status(message_id):
    user = auth.get_current_user()
    status = request.form.get("status", "")
    if status not in ("accepted", "declined", "pending"):
        flash(t("compte.flash_status_invalid"), "error")
        return redirect(url_for("compte.home"))
    updated, payment_result = _process_application_status(message_id, user, status)
    if not updated:
        flash(t("compte.flash_status_update_fail"), "error")
    else:
        flash(t("compte.flash_status_updated"), "success")
        if payment_result and payment_result.get("invoice_url"):
            flash(t("compte.flash_invoice_sent"), "success")
            return redirect(payment_result["invoice_url"])
        if payment_result and payment_result.get("payment_error"):
            flash(t("compte.flash_payment_error", error=payment_result['payment_error']), "warning")
    return redirect(url_for("compte.message_detail", message_id=message_id))


# ── Messagerie API (entreprise ↔ startup) ──


@compte_bp.route("/compte/api/messaging/poll")
@api_login_required()
def messaging_poll(user):
    since = request.args.get("since", "")
    data = store.get_messaging_poll(user["id"], since)
    return jsonify({"ok": True, **data})


@compte_bp.route("/compte/api/messaging/thread")
@api_login_required()
def messaging_thread(user):
    counterpart_id = request.args.get("counterpart", "").strip()
    project_id = request.args.get("project_id") or None
    if not counterpart_id:
        return jsonify({"ok": False, "error": "Destinataire requis."}), 400

    counterpart = store.get_user(counterpart_id)
    if not counterpart:
        return jsonify({"ok": False, "error": "Utilisateur introuvable."}), 404

    messages = store.get_thread_messages(user["id"], counterpart_id, project_id)
    if messages:
        store.mark_thread_read(user["id"], counterpart_id, project_id)

    return jsonify({
        "ok": True,
        "counterpart": {
            "id": counterpart["id"],
            "name": store._profile_name_for_user(counterpart),
            "role": counterpart.get("role", ""),
        },
        "project_id": project_id,
        "messages": [store.serialize_message_api(m, user["id"]) for m in messages],
    })


@compte_bp.route("/compte/api/messaging/send", methods=["POST"])
@api_login_required()
def messaging_send(user):
    payload = request.get_json(silent=True) or {}
    counterpart_id = (payload.get("counterpart_user_id") or "").strip()
    body = (payload.get("body") or "").strip()
    project_id = payload.get("project_id") or None

    if not counterpart_id or not body:
        return jsonify({"ok": False, "error": "Destinataire et message requis."}), 400

    recipient = store.get_user(counterpart_id)
    if not recipient:
        return jsonify({"ok": False, "error": "Destinataire introuvable."}), 404

    try:
        msg = store.send_b2b_message(user, recipient, body, project_id=project_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({
        "ok": True,
        "message": store.serialize_message_api(msg, user["id"]),
        "unread": store.get_unread_count(user["id"]),
    })


@compte_bp.route("/compte/api/messaging/read", methods=["POST"])
@api_login_required()
def messaging_mark_read(user):
    payload = request.get_json(silent=True) or {}
    counterpart_id = (payload.get("counterpart_user_id") or "").strip()
    project_id = payload.get("project_id") or None
    if not counterpart_id:
        return jsonify({"ok": False, "error": "Destinataire requis."}), 400
    store.mark_thread_read(user["id"], counterpart_id, project_id)
    return jsonify({"ok": True, "unread": store.get_unread_count(user["id"])})


@compte_bp.route("/compte/api/messaging/<message_id>/status", methods=["POST"])
@api_login_required(role="enterprise")
def messaging_update_status(user, message_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status", "")
    if status not in ("accepted", "declined", "pending"):
        return jsonify({"ok": False, "error": "Statut invalide."}), 400
    updated, payment_result = _process_application_status(message_id, user, status)
    if not updated:
        return jsonify({"ok": False, "error": "Impossible de mettre à jour."}), 400
    response = {
        "ok": True,
        "message": store.serialize_message_api(updated, user["id"]),
    }
    if payment_result:
        response["payment"] = {
            "invoice_url": payment_result.get("invoice_url"),
            "engagement_id": (payment_result.get("engagement") or {}).get("id"),
            "error": payment_result.get("payment_error"),
        }
    return jsonify(response)


@compte_bp.route("/compte/startup/stripe/onboard")
@auth.login_required(role="startup")
def startup_stripe_onboard():
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    if not profile:
        return redirect(url_for("vitrine.index"))
    if not stripe_service.is_configured():
        flash(t("compte.flash_stripe_not_configured"), "error")
        return redirect(url_for("compte.startup_dashboard"))
    try:
        url = stripe_service.create_connect_onboarding_link(profile, user)
        return redirect(url)
    except stripe_service.PaymentError as exc:
        flash(str(exc), "error")
        return redirect(url_for("compte.startup_dashboard"))


@compte_bp.route("/compte/startup/stripe/return")
@auth.login_required(role="startup")
def startup_stripe_return():
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    if profile:
        stripe_service.refresh_connect_status(profile)
    flash(t("compte.flash_stripe_updated"), "success")
    return redirect(url_for("compte.startup_dashboard"))


@compte_bp.route("/compte/startup/stripe/refresh")
@auth.login_required(role="startup")
def startup_stripe_refresh():
    flash(t("compte.flash_stripe_resume"), "info")
    return redirect(url_for("compte.startup_stripe_onboard"))


@compte_bp.route("/compte/entreprise/abonnement/pro")
@auth.login_required(role="enterprise")
def enterprise_subscribe_pro():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_ent_missing"), "error")
        return redirect(url_for("vitrine.index"))
    if not stripe_service.is_configured():
        flash(t("compte.flash_payments_disabled"), "warning")
        return redirect(url_for("compte.enterprise_dashboard"))

    from payments import subscriptions
    from payments.pricing_plans import is_pro_enterprise

    profile = subscriptions.sync_enterprise_subscription(profile) or profile
    if is_pro_enterprise(profile):
        flash(t("compte.flash_pro_already_active"), "info")
        return redirect(url_for("compte.enterprise_billing_portal"))

    try:
        url = subscriptions.create_pro_subscription_checkout(profile, user)
    except stripe_service.PaymentError as exc:
        flash(str(exc), "error")
        return redirect(url_for("compte.enterprise_dashboard"))

    return redirect(url)


@compte_bp.route("/compte/entreprise/abonnement/succes")
@auth.login_required(role="enterprise")
def enterprise_subscribe_success():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    session_id = request.args.get("session_id", "").strip()

    if session_id and stripe_service.is_configured():
        from payments import subscriptions

        try:
            checkout_session = stripe_service.retrieve_checkout_session(session_id)
            result = subscriptions.complete_checkout_subscription(checkout_session)
            if result.get("ok"):
                flash(t("compte.flash_pro_activated"), "success")
                return redirect(url_for("compte.enterprise_dashboard"))
        except stripe_service.PaymentError:
            pass

    if profile:
        from payments import subscriptions

        refreshed = subscriptions.sync_enterprise_subscription(profile)
        if refreshed and refreshed.get("plan") == "pro_enterprise":
            flash(t("compte.flash_pro_activated"), "success")
        else:
            flash(t("compte.flash_pro_confirming"), "info")

    return redirect(url_for("compte.enterprise_dashboard"))


@compte_bp.route("/compte/entreprise/abonnement")
@auth.login_required(role="enterprise")
def enterprise_billing_portal():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    if not profile:
        flash(t("compte.flash_profile_ent_missing"), "error")
        return redirect(url_for("vitrine.index"))
    if not stripe_service.is_configured():
        flash(t("compte.flash_billing_unavailable"), "warning")
        return redirect(url_for("compte.enterprise_dashboard"))

    from payments import subscriptions

    try:
        url = subscriptions.create_billing_portal_session(profile, user)
    except stripe_service.PaymentError as exc:
        flash(str(exc), "error")
        return redirect(url_for("compte.enterprise_dashboard"))

    return redirect(url)


@compte_bp.route("/compte/engagements/<engagement_id>/release", methods=["POST"])
@auth.login_required(role="enterprise")
def release_engagement_funds(engagement_id):
    user = auth.get_current_user()
    result = payment_handlers.release_engagement(engagement_id, user)
    if result.get("ok"):
        flash(t("compte.flash_funds_released"), "success")
    else:
        flash(result.get("error", t("compte.flash_release_error")), "error")
    engagement = store.get_engagement(engagement_id)
    if engagement and engagement.get("application_message_id"):
        return redirect(url_for(
            "compte.message_detail",
            message_id=engagement["application_message_id"],
        ))
    return redirect(url_for("compte.enterprise_dashboard"))
