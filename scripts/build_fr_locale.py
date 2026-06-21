import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
en = json.loads((ROOT / "vitrine/locales/en.json").read_text(encoding="utf-8"))

fr = json.loads(json.dumps(en))
fr["nav"].update({
    "home": "Accueil", "enterprises": "Entreprises", "startups": "Startups",
    "projects": "Projets", "about": "À propos", "login": "Connexion",
    "signup": "Inscription", "signup_enterprise": "Entreprise",
    "signup_enterprise_desc": "Publier un projet IoT", "signup_startup": "Startup",
    "signup_startup_desc": "Trouver des missions", "contact": "Contact",
    "messages": "Messages", "menu": "Menu", "home_aria": "Iotplace — Accueil",
    "lang": "Langue", "lang_en": "EN", "lang_fr": "FR",
})
fr["compte"] = {
    "login_title": "Connexion",
    "login_sub": "Accédez à votre espace entreprise ou startup.",
    "email": "Email",
    "password": "Mot de passe",
    "login_btn": "Se connecter",
    "no_account": "Pas encore de compte ?",
    "register_enterprise": "Inscription entreprise",
    "register_startup": "Inscription startup",
    "email_ph": "vous@entreprise.com",
    "flash_login_ok": "Connexion réussie.",
    "flash_login_fail": "Email ou mot de passe incorrect.",
    "flash_logout": "Vous êtes déconnecté.",
    "register_ent_title": "Inscription entreprise",
    "register_ent_sub": "Créez votre compte donneur d'ordre et publiez vos besoins IoT.",
    "register_st_title": "Inscription startup",
    "register_st_sub": "Créez votre profil startup et accédez aux missions IoT.",
    "already_registered": "Déjà inscrit ?",
    "login_link": "Se connecter",
    "submit_register": "Créer mon compte",
    "choose": "— Choisir —",
    "employees": "employés",
}

en.setdefault("nav", {}).update({"lang": "Language", "lang_en": "EN", "lang_fr": "FR"})
en["compte"] = {
    "login_title": "Log in",
    "login_sub": "Access your enterprise or startup account.",
    "email": "Email",
    "password": "Password",
    "login_btn": "Log in",
    "no_account": "No account yet?",
    "register_enterprise": "Enterprise signup",
    "register_startup": "Startup signup",
    "email_ph": "you@company.com",
    "flash_login_ok": "Logged in successfully.",
    "flash_login_fail": "Incorrect email or password.",
    "flash_logout": "You have been logged out.",
    "register_ent_title": "Enterprise signup",
    "register_ent_sub": "Create your client account and publish your IoT needs.",
    "register_st_title": "Startup signup",
    "register_st_sub": "Create your startup profile and access IoT missions.",
    "already_registered": "Already registered?",
    "login_link": "Log in",
    "submit_register": "Create my account",
    "choose": "— Choose —",
    "employees": "employees",
}

(ROOT / "vitrine/locales/fr.json").write_text(json.dumps(fr, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "vitrine/locales/en.json").write_text(json.dumps(en, ensure_ascii=False, indent=2), encoding="utf-8")
print("locales ok")
