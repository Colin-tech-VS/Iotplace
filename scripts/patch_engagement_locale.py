"""Add engagement journey i18n + compte phase field labels."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENGAGEMENT_EN = {
    "title": "The enterprise outsourcing journey",
    "subtitle": "What large groups actually look for: validate fast, then scale, then commit long term.",
    "intro": "Iotplace structures IoT subcontracting in three progressive phases — the model used by industrial leaders to de-risk outsourcing before committing volume.",
    "learn_more": "Details",
    "enterprise_seeks": "What enterprises seek:",
    "iotplace_offer": "How Iotplace supports you:",
    "journey_note": "Each phase can be a separate project on the platform. Startups see the phase upfront and can position for long-term partnership from the PoC.",
    "cta_enterprise": "Start with a PoC project",
    "cta_pricing": "See pricing per phase",
    "phase_label": "Engagement phase",
    "phase_hint": "Select the stage that matches your outsourcing intent. Budget and duration suggestions adapt automatically.",
    "filter_all": "All phases",
    "phases": {
        "poc": {
            "name": "Quick PoC",
            "short_label": "PoC",
            "duration": "3–6 months",
            "goal": "Validate technology, team and ROI on a limited scope before any large commitment.",
            "explain": "A bounded pilot: firmware bring-up, sensor prototype, cloud MVP or integration slice. Clear success criteria, fixed budget, go/no-go at the end.",
            "enterprise_seeks": "Proof of feasibility, startup responsiveness, quality of deliverables and fit with internal teams — without multi-year risk.",
            "iotplace_offer": "Free enterprise account, 1 active project, matching with agile IoT startups, escrow invoice on acceptance, 10% commission only if the PoC is signed.",
        },
        "scale": {
            "name": "Large-scale deployment",
            "short_label": "Scale",
            "duration": "6–18 months",
            "goal": "Roll out the validated solution to production volumes, sites or product lines after a successful PoC.",
            "explain": "Industrialisation, multi-site rollout, supply chain, certification, DevOps and sustained engineering capacity from the same startup or a broader shortlist.",
            "enterprise_seeks": "Repeatable delivery, capacity to scale teams, project governance and predictable costs across regions or business units.",
            "iotplace_offer": "Multi-project tracking, escrow on each tranche, optional Enterprise Pro for unlimited publications and 7% commission, dedicated support for active outsourcers.",
        },
        "partnership": {
            "name": "Long-term commercial partnership",
            "short_label": "Partnership",
            "duration": "12+ months · renewable",
            "goal": "Embed a startup (or pool) as a strategic subcontractor for ongoing IoT roadmap execution.",
            "explain": "After strong PoC and scale results: framework agreement, preferred rates, continuous backlog of firmware/hardware/cloud missions, co-innovation on the IoT roadmap.",
            "enterprise_seeks": "A trusted extension of their engineering capacity in Asia, reduced sourcing friction, aligned incentives and multi-year cost optimisation.",
            "iotplace_offer": "Enterprise Pro, reduced commission (7%), priority matching, structured partnership projects on Iotplace, Stripe Connect payouts and escrow on each mission.",
        },
    },
}

ENGAGEMENT_FR = {
    "title": "Le parcours de sous-traitance entreprise",
    "subtitle": "Ce que les grands groupes recherchent : valider vite, déployer à l'échelle, puis s'engager sur le long terme.",
    "intro": "Iotplace structure la sous-traitance IoT en trois phases progressives — le modèle des industriels pour réduire le risque avant d'engager des volumes.",
    "learn_more": "En savoir plus",
    "enterprise_seeks": "Ce que l'entreprise recherche :",
    "iotplace_offer": "Comment Iotplace vous accompagne :",
    "journey_note": "Chaque phase peut être un projet distinct sur la plateforme. Les startups voient la phase dès le départ et peuvent se positionner pour un partenariat long terme dès le PoC.",
    "cta_enterprise": "Démarrer par un PoC",
    "cta_pricing": "Voir les tarifs par phase",
    "phase_label": "Phase d'engagement",
    "phase_hint": "Choisissez l'étape qui correspond à votre intention de sous-traitance. Budget et durée sont suggérés automatiquement.",
    "filter_all": "Toutes les phases",
    "phases": {
        "poc": {
            "name": "PoC rapide",
            "short_label": "PoC",
            "duration": "3 à 6 mois",
            "goal": "Valider la technologie, l'équipe et le ROI sur un périmètre limité avant tout engagement majeur.",
            "explain": "Pilote borné : firmware, prototype capteur, MVP cloud ou tranche d'intégration. Critères de succès clairs, budget fixe, décision go/no-go en fin de phase.",
            "enterprise_seeks": "Preuve de faisabilité, réactivité startup, qualité des livrables et adéquation avec les équipes internes — sans risque pluriannuel.",
            "iotplace_offer": "Compte entreprise gratuit, 1 projet actif, matching startups IoT agiles, facture séquestre à l'acceptation, 10 % de commission uniquement si le PoC est signé.",
        },
        "scale": {
            "name": "Déploiement à grande échelle",
            "short_label": "Scale",
            "duration": "6 à 18 mois",
            "goal": "Déployer la solution validée en production, sur les sites ou gammes produits, après un PoC réussi.",
            "explain": "Industrialisation, déploiement multi-sites, supply chain, certification, DevOps et capacité d'ingénierie soutenue avec la même startup ou un panel élargi.",
            "enterprise_seeks": "Livraison répétable, capacité à monter en charge, gouvernance projet et coûts prévisibles sur plusieurs sites ou BU.",
            "iotplace_offer": "Suivi multi-projets, séquestre par tranche, option Entreprise Pro (projets illimités, 7 % de commission), support dédié pour les donneurs d'ordre actifs.",
        },
        "partnership": {
            "name": "Partenariat commercial long terme",
            "short_label": "Partenariat",
            "duration": "12+ mois · renouvelable",
            "goal": "Intégrer une startup (ou un pool) comme sous-traitant stratégique pour la roadmap IoT continue.",
            "explain": "Après PoC et scale réussis : accord-cadre, tarifs préférentiels, backlog continu firmware/hardware/cloud, co-innovation sur la roadmap IoT.",
            "enterprise_seeks": "Une extension de confiance de leur capacité d'ingénierie en Asie, moins de friction sourcing, incitations alignées et optimisation des coûts sur plusieurs années.",
            "iotplace_offer": "Entreprise Pro, commission réduite (7 %), matching prioritaire, projets partenariat structurés sur Iotplace, paiements Stripe Connect et séquestre par mission.",
        },
    },
}

COMPTE_EXTRA = {
    "en": {
        "project_engagement_phase": "Engagement phase",
        "project_engagement_phase_ph": "— Select phase —",
    },
    "fr": {
        "project_engagement_phase": "Phase d'engagement",
        "project_engagement_phase_ph": "— Choisir la phase —",
    },
}

for fname, engagement, compte_extra in [
    ("en.json", ENGAGEMENT_EN, COMPTE_EXTRA["en"]),
    ("fr.json", ENGAGEMENT_FR, COMPTE_EXTRA["fr"]),
]:
    path = ROOT / "vitrine/locales" / fname
    data = json.loads(path.read_text(encoding="utf-8"))
    data["engagement"] = engagement
    data["compte"].update(compte_extra)
    if "pricing" in data:
        data["pricing"]["offers_title"] = (
            "Plans aligned with your journey" if fname == "en.json" else "Offres alignées sur votre parcours"
        )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("patched", fname)
