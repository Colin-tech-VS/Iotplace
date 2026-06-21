from flask import flash, redirect, render_template, request, url_for

import auth
from compte import compte_bp
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
    projects = store.get_projects_for_enterprise(profile["id"], profile.get("name", ""))
    return render_template(
        "compte/dashboard_enterprise.html",
        user=user,
        profile=profile,
        projects=projects,
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
    matching = store.get_matching_projects_for_startup(profile)
    return render_template(
        "compte/dashboard_startup.html",
        user=user,
        profile=profile,
        matching_projects=matching,
    )


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
            "skills": store.parse_list_field(request.form.get("skills")),
        })
        flash("Profil mis à jour.", "success")
        return redirect(url_for("compte.startup_dashboard"))

    return render_template("compte/edit_startup.html", user=user, profile=profile)
