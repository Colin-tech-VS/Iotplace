from flask import flash, jsonify, redirect, render_template, request, url_for

import auth
from compte import compte_bp
from compte.api_auth import api_login_required
from data import store

def _validate_credentials(email, password, password_confirm=None):
    errors = []
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        errors.append("Email invalide.")
    if not password or len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères.")
    if password_confirm is not None and password != password_confirm:
        errors.append("Les mots de passe ne correspondent pas.")
    if email and store.email_exists(email):
        errors.append("Un compte existe déjà avec cet email.")
    return errors


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
            flash("Connexion réussie.", "success")
            next_url = request.args.get("next") or url_for("compte.home")
            return redirect(next_url)
        flash("Email ou mot de passe incorrect.", "error")

    return render_template("compte/login.html")


@compte_bp.route("/deconnexion")
def logout():
    auth.logout_user()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("vitrine.index"))


@compte_bp.route("/compte")
def home():
    user = auth.get_current_user()
    if not user:
        return redirect(url_for("compte.login"))
    if user["role"] == "enterprise":
        return redirect(url_for("compte.enterprise_dashboard"))
    return redirect(url_for("compte.startup_dashboard"))


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
            errors.append("Le nom de l'entreprise est requis.")
        if not request.form.get("contact_name", "").strip():
            errors.append("Le nom du contact est requis.")

        has_project = request.form.get("has_project") == "yes"
        if has_project and not request.form.get("project_title", "").strip():
            errors.append("Le titre du projet est requis si vous publiez un besoin.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("compte/register_enterprise.html", form=dict(request.form))

        try:
            project_fields = None
            if has_project:
                project_fields = {
                    "title": request.form.get("project_title", "").strip(),
                    "description": request.form.get("project_description", "").strip(),
                    "budget": request.form.get("project_budget", "").strip(),
                    "duration": request.form.get("project_duration", "").strip(),
                    "skills": store.parse_list_field(request.form.get("project_skills")),
                }

            user, _profile = store.register_enterprise_account(
                {
                    "email": request.form.get("email", "").strip().lower(),
                    "password_hash": auth.hash_password(request.form.get("password", "")),
                },
                {
                    "name": request.form.get("company_name", "").strip(),
                    "sector": request.form.get("sector", "").strip(),
                    "country": request.form.get("country", "").strip(),
                    "city": request.form.get("city", "").strip(),
                    "company_size": request.form.get("company_size", "").strip(),
                    "contact_name": request.form.get("contact_name", "").strip(),
                    "contact_role": request.form.get("contact_role", "").strip(),
                    "phone": request.form.get("phone", "").strip(),
                    "website": request.form.get("website", "").strip(),
                    "email": request.form.get("email", "").strip().lower(),
                    "description": request.form.get("description", "").strip(),
                    "besoin": request.form.get("besoin", "").strip(),
                    "needs": store.parse_list_field(request.form.get("needs")),
                },
                project_fields,
            )
            auth.login_user(user)
            flash("Bienvenue ! Votre espace entreprise est prêt.", "success")
            return redirect(url_for("compte.enterprise_dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("compte/register_enterprise.html", form=dict(request.form))

    return render_template("compte/register_enterprise.html", form={})


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
            errors.append("Le nom de la startup est requis.")
        if not request.form.get("country", "").strip():
            errors.append("Le pays est requis.")
        if not request.form.get("specialty", "").strip():
            errors.append("La spécialité IoT est requise.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("compte/register_startup.html", form=dict(request.form))

        try:
            user, _profile = store.register_startup_account(
                {
                    "email": request.form.get("email", "").strip().lower(),
                    "password_hash": auth.hash_password(request.form.get("password", "")),
                },
                {
                    "name": request.form.get("startup_name", "").strip(),
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
                },
            )
            auth.login_user(user)
            flash("Bienvenue ! Votre espace startup est prêt.", "success")
            return redirect(url_for("compte.startup_dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("compte/register_startup.html", form=dict(request.form))

    return render_template("compte/register_startup.html", form={})


@compte_bp.route("/compte/entreprise")
@auth.login_required(role="enterprise")
def enterprise_dashboard():
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    if not profile:
        flash("Profil entreprise introuvable.", "error")
        return redirect(url_for("vitrine.index"))
    dash = store.get_dashboard_data_for_enterprise(user, profile)
    return render_template(
        "compte/dashboard_enterprise.html",
        user=user,
        profile=profile,
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
            flash("Le titre du projet est requis.", "error")
            return render_template("compte/project_form.html", profile=profile, user=user, form=dict(request.form))
        store.add_project_for_enterprise(profile, {
            "title": title,
            "description": request.form.get("description", "").strip(),
            "budget": request.form.get("budget", "").strip(),
            "duration": request.form.get("duration", "").strip(),
            "skills": store.parse_list_field(request.form.get("skills")),
            "status": "Ouvert",
        })
        flash("Projet publié.", "success")
        return redirect(url_for("compte.enterprise_dashboard"))

    return render_template("compte/project_form.html", profile=profile, user=user, form={})


@compte_bp.route("/compte/entreprise/projet/<project_id>")
@auth.login_required(role="enterprise")
def enterprise_project_detail(project_id):
    user = auth.get_current_user()
    profile = store.get_enterprise_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project or project.get("enterprise_id") != profile["id"]:
        flash("Projet introuvable.", "error")
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
        flash("Profil entreprise introuvable.", "error")
        return redirect(url_for("vitrine.index"))

    if request.method == "POST":
        store.update_enterprise_profile(profile["id"], {
            "name": request.form.get("company_name", "").strip(),
            "sector": request.form.get("sector", "").strip(),
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
        flash("Profil mis à jour.", "success")
        return redirect(url_for("compte.enterprise_dashboard"))

    return render_template("compte/edit_enterprise.html", user=user, profile=profile)


@compte_bp.route("/compte/startup")
@auth.login_required(role="startup")
def startup_dashboard():
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    if not profile:
        flash("Profil startup introuvable.", "error")
        return redirect(url_for("vitrine.index"))
    dash = store.get_dashboard_data_for_startup(user, profile)
    return render_template(
        "compte/dashboard_startup.html",
        user=user,
        profile=profile,
        **dash,
    )


@compte_bp.route("/compte/startup/projet/<project_id>")
@auth.login_required(role="startup")
def startup_project_detail(project_id):
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project:
        flash("Projet introuvable.", "error")
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
    )


@compte_bp.route("/compte/startup/projet/<project_id>/postuler", methods=["POST"])
@auth.login_required(role="startup")
def startup_apply_project(project_id):
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    project = store.get_project(project_id)
    if not profile or not project:
        flash("Projet introuvable.", "error")
        return redirect(url_for("compte.startup_dashboard"))
    body = request.form.get("message", "").strip()
    if not body:
        flash("Ajoutez un message de présentation pour votre candidature.", "error")
        return redirect(url_for("compte.startup_project_detail", project_id=project_id))
    try:
        store.apply_to_project(user, profile, project, body)
        flash("Candidature envoyée à l'entreprise.", "success")
        return redirect(url_for("compte.startup_dashboard") + "#messages")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("compte.startup_project_detail", project_id=project_id))


@compte_bp.route("/compte/startup/profil", methods=["GET", "POST"])
@auth.login_required(role="startup")
def startup_edit_profile():
    user = auth.get_current_user()
    profile = store.get_startup_for_user(user["id"])
    if not profile:
        flash("Profil startup introuvable.", "error")
        return redirect(url_for("vitrine.index"))

    if request.method == "POST":
        store.update_startup_profile(profile["id"], {
            "name": request.form.get("startup_name", "").strip(),
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
        flash("Profil mis à jour.", "success")
        return redirect(url_for("compte.startup_dashboard"))

    return render_template("compte/edit_startup.html", user=user, profile=profile)


@compte_bp.route("/compte/messages/<message_id>")
@auth.login_required()
def message_detail(message_id):
    user = auth.get_current_user()
    msg = store.get_message(message_id)
    if not msg or user["id"] not in (msg.get("from_user_id"), msg.get("to_user_id")):
        flash("Message introuvable.", "error")
        return redirect(url_for("compte.home"))
    if msg.get("to_user_id") == user["id"] and not msg.get("read"):
        store.mark_message_read(message_id, user["id"])
    enriched = store.enrich_message_for_view(msg, user["id"])
    project = store.get_project(msg["project_id"]) if msg.get("project_id") else None
    return render_template(
        "compte/message_detail.html",
        user=user,
        message=enriched,
        project=project,
    )


@compte_bp.route("/compte/messages/<message_id>/repondre", methods=["POST"])
@auth.login_required()
def message_reply(message_id):
    user = auth.get_current_user()
    original = store.get_message(message_id)
    if not original or user["id"] not in (original.get("from_user_id"), original.get("to_user_id")):
        flash("Message introuvable.", "error")
        return redirect(url_for("compte.home"))
    body = request.form.get("body", "").strip()
    if not body:
        flash("Le message ne peut pas être vide.", "error")
        return redirect(url_for("compte.message_detail", message_id=message_id))
    recipient_id = (
        original["from_user_id"]
        if original.get("to_user_id") == user["id"]
        else original["to_user_id"]
    )
    recipient = store.get_user(recipient_id)
    if not recipient:
        flash("Destinataire introuvable.", "error")
        return redirect(url_for("compte.message_detail", message_id=message_id))
    project = store.get_project(original["project_id"]) if original.get("project_id") else None
    subject = f"Re: {original.get('subject', 'Message')}"
    store.send_message(user, recipient, subject, body, kind="reply", project=project)
    flash("Réponse envoyée.", "success")
    return redirect(url_for("compte.message_detail", message_id=message_id))


@compte_bp.route("/compte/messages/<message_id>/statut", methods=["POST"])
@auth.login_required(role="enterprise")
def message_update_status(message_id):
    user = auth.get_current_user()
    status = request.form.get("status", "")
    if status not in ("accepted", "declined", "pending"):
        flash("Statut invalide.", "error")
        return redirect(url_for("compte.home"))
    updated = store.update_message_status(message_id, user["id"], status)
    if not updated:
        flash("Impossible de mettre à jour ce message.", "error")
    else:
        flash("Statut de la candidature mis à jour.", "success")
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
    updated = store.update_message_status(message_id, user["id"], status)
    if not updated:
        return jsonify({"ok": False, "error": "Impossible de mettre à jour."}), 400
    return jsonify({
        "ok": True,
        "message": store.serialize_message_api(updated, user["id"]),
    })
