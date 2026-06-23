# Iotplace — Analyse globale & indications pour la suite

Document de référence (état au juin 2026). À relire avant une phase de croissance, une levée ou un gros push marketing.

---

## Verdict global

**Oui, ça peut marcher** — surtout en **pilote B2B** (dizaines à quelques centaines d’utilisateurs actifs), avec Postgres/Supabase bien configuré, Stripe en prod, et un positionnement clair (matching IoT entreprise ↔ startup).

Ce n’est **pas encore une plateforme “scale-up”** prête pour un gros trafic marketing ou des centaines d’utilisateurs simultanés sans friction. Le produit est riche ; l’architecture données reste le goulot principal.

---

## Ce qui est solide (et rare pour un MVP)

| Domaine | État |
|--------|------|
| **Parcours métier** | Inscription → profil → projet → candidature → acceptation → facture → escrow → release → suivi d’avancement |
| **Paiements** | Stripe Checkout (PoC), abonnement Pro, Connect pour startups, webhooks |
| **Matching** | Scoring sector/skills/needs, dashboards avec recommandations |
| **Messagerie** | Threads B2B, statuts candidature, intégration paiement dans les messages |
| **Vitrine / SEO** | i18n FR/EN, sitemap, robots, JSON-LD, domaines IoT, llms.txt, annuaires |
| **CRM** | Contenu, SEO IA, mailing, analytics, gestion comptes |
| **Profils** | Logo, vérification SIREN/SIRET, complétion profil (onglets, %) |
| **Ops** | Scalingo, release check, migrations, scripts demo + smoke test |

Pour une **marketplace B2B IoT en Asie du Sud-Est**, le positionnement produit est cohérent et différenciant.

---

## Architecture (rappel technique)

```
Browser / Stripe webhooks
        ↓
Gunicorn (2 workers) → Flask (app.py)
        ├── vitrine_bp   (site public, advisor, SEO)
        ├── compte_bp    (dashboards, messagerie, profils)
        ├── crm_bp       (admin /crm)
        └── payments_bp  (webhooks Stripe)
        ↓
data/store.py (~3 600 lignes) — logique métier
        ↓
data/persistence.py
        ├── PostgreSQL JSONB (iotplace_state, id=1)  ← prod recommandé
        ├── Supabase REST + Storage (logos)
        └── data/content.json                        ← dev uniquement
```

**Services externes :** Mistral AI, Stripe, SMTP/IMAP (CRM), API Entreprises (SIREN/SIRET).

---

## Ce qui limitera (ou cassera) à moyenne échelle

### 1. Modèle de données “tout-en-un JSON”

Tout l’état applicatif vit dans **un blob JSONB** (`iotplace_state`). Chaque message lu, chaque vue analytics, chaque sauvegarde profil = **rechargement + réécriture du document entier**.

- OK aujourd’hui (~quelques dizaines de profils)
- Risque à **2 workers Gunicorn** : écritures concurrentes → **perte de données** sans verrou optimiste
- Plafond réaliste : **quelques centaines d’utilisateurs actifs** avant latence et fiabilité problématiques

### 2. Pas de vraie suite de tests / CI

- `scripts/flow_check.py` = smoke test manuel ou CI possible
- **Pas de pytest** ni pipeline GitHub Actions aujourd’hui
- Les régressions (Stripe, matching, profil) peuvent passer en prod sans alerte

### 3. Sécurité partielle

| Problème | Détail |
|----------|--------|
| Redirect `next` | Login compte : `request.args.get("next")` non validé (le CRM utilise `safe_next_url`) |
| CSRF CRM | Uniquement sur le login ; autres POST admin non protégés |
| Rate limit advisor | En mémoire → inefficace avec 2 workers |
| Supabase | Grants `anon` larges sur `iotplace_state`, RLS commenté dans la migration |

### 4. Bug connu — logos profil

**Fichier :** `compte/profile_media.py` ligne 70

Dans le fallback Supabase → local, `relative` est utilisé au lieu de `path` → crash si Supabase Storage échoue.

```python
# À corriger :
return _upload_local(data, path)  # pas relative
```

### 5. Ops incomplets

- `scripts/send_progress_reminders.py` existe mais **pas de cron Scalingo** dans le `Procfile`
- Pas d’endpoint `/health` pour monitoring
- Pas de Sentry / alertes erreurs
- `scripts/release_check.py` **warn** si pas de `DATABASE_URL` au lieu de **bloquer** le deploy

### 6. Stripe

- Pas d’idempotence webhook (`event.id` non stocké) → retries Stripe peuvent double-appliquer
- États `payment_error` / engagement orphelin possibles si facture échoue après acceptation

### 7. Rate limits & lockouts

CRM login lockout et advisor rate limit sont **par processus** → non partagés entre workers Gunicorn.

---

## Par axe : état & pistes

### Produit & UX

**Très bon pour un MVP.** Dashboards entreprise/startup, escrow dans la messagerie, suivi de mission.

**À ajouter :**

- Notifications email sur nouvelle candidature, facture, message (au-delà des rappels de progression)
- Export PDF contrat / bon de commande
- Timeline candidature côté startup
- Recherche unifiée vitrine (“trouver une startup / un projet”)
- Onboarding guidé post-inscription (checklist “publiez votre 1er projet”)

### Matching

Heuristique (tokens + synonymes firmware/LoRaWAN/MQTT…). Suffisant pour démarrer.

**Améliorer :**

- Index inversé `{skill → startup_ids}`
- Feedback utilisateur sur les recommandations
- Pondération géo / langue
- Cache des matchs par requête (`flask.g` ou Redis)
- À long terme : embeddings (Mistral / pgvector)

### Chatbot IA (Copilote)

Mistral + `site_knowledge` + matching live sur intentions détectées. Différenciateur marketing.

**Améliorer :**

- Rate limit Redis (pas mémoire)
- RAG par sections (éviter d’injecter tout le JSON à chaque requête)
- Afficher les `matches` structurés dans l’UI advisor (`advisor.js`)

### SEO & acquisition

Sitemap avec `lastmod`, projets fermés exclus, domaines, JSON-LD, llms.txt, OG profils.

**Encore à faire :**

- Blog / cas clients
- Pages pays (“startups IoT Vietnam”)
- Core Web Vitals : bundle CSS, fonts self-hosted
- Backlinks et contenu éditorial régulier

### Performance (déjà partiellement fait)

- Cache static 1 an, logos 24h
- Scripts `defer`, page loader allégé
- Analytics throttled (45s/session)
- `get_unread_count` et index projets/entreprises optimisés
- API `/api/directory/search`

**Suite :**

- Réduire les `_save_raw` (analytics hors blob ou buffer)
- CSS conditionnel par page (messenger.css, advisor.css seulement où nécessaire)
- Resize logos WebP à l’upload

### Paiements

Flux escrow crédible pour pilote.

**Durcir :**

- Idempotence webhooks
- Tests automatisés checkout + webhook
- Flux litige / remboursement documenté

---

## Variables d’environnement critiques (prod)

| Variable | Rôle |
|----------|------|
| `SECRET_KEY` | Sessions Flask |
| `SITE_URL` | Canonical, Stripe return URLs |
| `DATABASE_URL` | **Obligatoire** — persistance Postgres |
| `CRM_ADMIN_USERNAME` / `CRM_ADMIN_PASSWORD` | Admin CRM (release check) |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` | Paiements |
| `STRIPE_WEBHOOK_SECRET` | Factures / abonnements |
| `MISTRAL_API_KEY` | Copilote + vérif IA |
| `SMTP_*` | Reset password, rappels, CRM mailing |
| `SUPABASE_URL` + `SUPABASE_KEY` | Storage logos (optionnel si local) |

**Ne jamais déployer sur Scalingo sans `DATABASE_URL`** — sinon données perdues au restart.

---

## Comptes démo

- Emails : `demo-ent-001@demo.iotplace.test` … `demo-st-050@demo.iotplace.test`
- Mot de passe : `DemoIotplace2025!`
- Script : `scripts/seed_demo_profiles.py`

---

## Scripts utiles

| Script | Usage |
|--------|--------|
| `scripts/flow_check.py` | Smoke test parcours entreprise + startup |
| `scripts/release_check.py` | Vérif env avant deploy Scalingo |
| `scripts/db_migrate.py` | Schéma Postgres |
| `scripts/send_progress_reminders.py` | Emails rappel progression (à cronner) |
| `scripts/seed_demo_profiles.py` | 50+50 profils démo |

---

## Scénarios : est-ce que ça marchera ?

| Scénario | Verdict |
|----------|---------|
| Demo / 50 comptes test, pitch investisseurs | ✅ Oui |
| 10–30 vraies entreprises + 50 startups, flux assisté | ✅ Oui (Postgres + Stripe) |
| Campagne marketing → 500+ inscriptions/mois | ⚠️ Risqué sans refonte data + monitoring |
| Plusieurs dynos Scalingo en parallèle | ❌ Pas safe (concurrence JSON) |
| Levée + scale régional | 🔧 Faisable après normalisation DB (3–6 mois) |

---

## Roadmap priorisée

### P0 — Critique (avant grosse mise en prod)

1. **Bloquer deploy sans `DATABASE_URL`** — modifier `release_check.py` (warning → error)
2. **Verrou optimiste sur `iotplace_state`** — champ `updated_at`, compare-and-swap avant `_save_raw`
3. **Fix `profile_media.py`** — `path` au lieu de `relative` ligne 70
4. **Idempotence webhooks Stripe** — table ou liste `processed_event_ids`

### P1 — Haute priorité

5. **CI GitHub Actions** — `python scripts/flow_check.py` à chaque push sur `main`
6. **Sécurité compte** — valider `next` redirect ; CSRF sur POST CRM/compte sensibles
7. **Cron Scalingo** — `send_progress_reminders.py` (ex. quotidien 9h UTC)
8. **`GET /health`** — retourne 200 + backend persistence
9. **Sentry** (ou équivalent) — erreurs 500 en prod

### P2 — Moyen terme

10. **Redis** — sessions, rate limits, cache matching
11. **Normalisation schema** — tables `users`, `messages`, `engagements`, `analytics` séparées
12. **Emails async** — file d’attente au lieu de SMTP synchrone dans la requête
13. **RLS Supabase** — retirer grants `anon` sur `iotplace_state`, service role only
14. **GDPR** — export / suppression compte self-service

### P3 — Stratégique

15. **WebSockets ou SSE** — messagerie temps réel (moins de polling)
16. **Matching embeddings** — pgvector + Mistral
17. **Bundle assets** — 1–2 CSS/JS par surface (vitrine / compte)
18. **Blog + cas clients** — SEO long terme

---

## Plan en 3 sprints (suggestion)

### Sprint 1 — Sécurité & ops (1–2 semaines)

- P0 #1, #3, #4
- `/health` + Sentry
- Cron rappels progression
- CI `flow_check`

### Sprint 2 — Fiabilité paiements & données (2–3 semaines)

- P0 #2 (verrou optimiste)
- Tests Stripe webhook
- Redirect `next` + CSRF
- Runbook backup JSONB Postgres

### Sprint 3 — Scale & produit (1–2 mois)

- Début normalisation tables messages/engagements
- Redis rate limits
- Notifications email candidatures
- Onboarding guidé

---

## Fichiers clés à connaître

| Fichier | Rôle |
|---------|------|
| `app.py` | App Flask, cache static, context processors |
| `data/store.py` | Toute la logique métier + persistance |
| `data/matching.py` | Scoring startups ↔ projets |
| `data/persistence.py` | Postgres / Supabase / JSON |
| `payments/handlers.py` | Orchestration Stripe |
| `vitrine/advisor_ai.py` | Copilote Mistral |
| `vitrine/routes.py` | SEO, sitemap, advisor API |
| `compte/routes.py` | Dashboards, messagerie |
| `crm/routes.py` | Admin |
| `Procfile` | Deploy Scalingo |
| `supabase/migrations/001_iotplace_state.sql` | Schéma JSONB |

---

## En une phrase

**Iotplace est un MVP B2B remarquablement complet** — le produit est prêt à être testé sur le marché ; la **technique doit encore “durcir”** (persistance obligatoire, concurrence, tests, sécurité, observabilité) avant une vraie phase de croissance.

---

*Dernière mise à jour : juin 2026 — après optimisations perf/SEO/matching/advisor (commit `84735bb` et suivants).*
