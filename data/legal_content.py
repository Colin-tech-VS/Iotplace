"""Default legal page bodies (FR / EN) — editable via CRM."""

from data.site_config import CONTACT_EMAIL

LEGAL_COMPANY = {
    "name": "Iotplace",
    "form": "SARL, société à responsabilité limitée",
    "siren": "980 867 485",
    "siret": "980 867 485 00016",
    "vat": "FR88980867485",
    "rcs": "980 867 485 R.C.S. Nanterre",
    "rcs_date": "26/10/2023",
    "email": CONTACT_EMAIL,
    "host": "Scalingo SAS",
    "host_address": "13 rue de la Tour des Dames, 75009 Paris, France",
    "host_site": "https://scalingo.com",
}


def _fr_mentions() -> str:
    c = LEGAL_COMPANY
    return f"""
<h2>1. Éditeur du site</h2>
<p>Le site <strong>iotplace.fr</strong> est édité par :</p>
<ul>
  <li><strong>{c['name']}</strong> — {c['form']}</li>
  <li>SIREN : {c['siren']}</li>
  <li>SIRET (siège) : {c['siret']}</li>
  <li>Numéro de TVA intracommunautaire : {c['vat']}</li>
  <li>Inscription au RCS : INSCRIT (greffe de Nanterre, le {c['rcs_date']})</li>
  <li>Numéro RCS : {c['rcs']}</li>
  <li>Inscription au RNE : INSCRIT</li>
  <li>Email : <a href="mailto:{c['email']}">{c['email']}</a></li>
</ul>

<h2>2. Directeur de la publication</h2>
<p>Le directeur de la publication est le gérant de la société {c['name']}.</p>

<h2>3. Hébergement</h2>
<p>Le site est hébergé par :</p>
<ul>
  <li><strong>{c['host']}</strong></li>
  <li>{c['host_address']}</li>
  <li>Site web : <a href="{c['host_site']}" rel="noopener noreferrer" target="_blank">{c['host_site']}</a></li>
</ul>

<h2>4. Propriété intellectuelle</h2>
<p>L'ensemble des éléments du site (textes, graphismes, logos, marques, structure) est protégé par le droit de la propriété intellectuelle. Toute reproduction ou représentation non autorisée constitue une contrefaçon.</p>

<h2>5. Limitation de responsabilité</h2>
<p>{c['name']} s'efforce d'assurer l'exactitude des informations publiées. Toutefois, la société ne saurait être tenue responsable des erreurs, omissions ou indisponibilités temporaires du service.</p>
<p>Les liens vers des sites tiers n'engagent pas la responsabilité de {c['name']} quant à leur contenu.</p>

<h2>6. Droit applicable</h2>
<p>Les présentes mentions légales sont régies par le droit français. En cas de litige, et à défaut de résolution amiable, les tribunaux français seront seuls compétents.</p>

<h2>7. Contact</h2>
<p>Pour toute question : <a href="/contact">formulaire de contact</a> ou <a href="mailto:{c['email']}">{c['email']}</a>.</p>
"""


def _en_legal() -> str:
    c = LEGAL_COMPANY
    return f"""
<h2>1. Website publisher</h2>
<p>The website <strong>iotplace.fr</strong> is published by:</p>
<ul>
  <li><strong>{c['name']}</strong> — French limited liability company (SARL)</li>
  <li>SIREN: {c['siren']}</li>
  <li>SIRET (head office): {c['siret']}</li>
  <li>VAT number: {c['vat']}</li>
  <li>Trade register (RCS Nanterre, registered {c['rcs_date']})</li>
  <li>RCS number: {c['rcs']}</li>
  <li>National business register (RNE): registered</li>
  <li>Email: <a href="mailto:{c['email']}">{c['email']}</a></li>
</ul>

<h2>2. Publication director</h2>
<p>The publication director is the managing director of {c['name']}.</p>

<h2>3. Hosting</h2>
<p>The website is hosted by:</p>
<ul>
  <li><strong>{c['host']}</strong></li>
  <li>{c['host_address']}</li>
  <li>Website: <a href="{c['host_site']}" rel="noopener noreferrer" target="_blank">{c['host_site']}</a></li>
</ul>

<h2>4. Intellectual property</h2>
<p>All site elements (text, graphics, logos, trademarks, structure) are protected by intellectual property law. Any unauthorised reproduction is prohibited.</p>

<h2>5. Limitation of liability</h2>
<p>{c['name']} endeavours to keep published information accurate but cannot be held liable for errors, omissions or temporary unavailability.</p>

<h2>6. Governing law</h2>
<p>These legal notices are governed by French law. French courts shall have exclusive jurisdiction.</p>

<h2>7. Contact</h2>
<p>Questions: <a href="/contact">contact form</a> or <a href="mailto:{c['email']}">{c['email']}</a>.</p>
"""


def _fr_privacy() -> str:
    c = LEGAL_COMPANY
    return f"""
<p><em>Dernière mise à jour : juin 2026</em></p>

<p>{c['name']} ({c['form']}, SIREN {c['siren']}) exploite la plateforme Iotplace, marketplace B2B IoT. La présente politique décrit comment nous traitons vos données personnelles conformément au RGPD et à la loi Informatique et Libertés.</p>

<h2>1. Responsable du traitement</h2>
<p>{c['name']} — {c['rcs']}<br>Email : <a href="mailto:{c['email']}">{c['email']}</a></p>

<h2>2. Données collectées</h2>
<ul>
  <li><strong>Formulaire de contact</strong> : nom, email, pays, type de profil, message.</li>
  <li><strong>Comptes utilisateurs</strong> : identité, coordonnées professionnelles, profil entreprise ou startup.</li>
  <li><strong>Navigation</strong> : pages visitées, durée de session (uniquement si vous acceptez les cookies analytiques).</li>
  <li><strong>Paiements</strong> : données traitées par Stripe (nous ne stockons pas vos coordonnées bancaires).</li>
</ul>

<h2>3. Finalités et bases légales</h2>
<ul>
  <li>Répondre à vos demandes — intérêt légitime / exécution de mesures précontractuelles.</li>
  <li>Gestion des comptes et missions — exécution du contrat.</li>
  <li>Amélioration du site — consentement (cookies analytiques).</li>
  <li>Obligations légales et comptables — obligation légale.</li>
</ul>

<h2>4. Durée de conservation</h2>
<ul>
  <li>Messages de contact : 3 ans à compter du dernier échange.</li>
  <li>Comptes actifs : durée de la relation contractuelle + 5 ans (prescription).</li>
  <li>Données analytiques : 13 mois maximum.</li>
</ul>

<h2>5. Destinataires</h2>
<p>Vos données sont accessibles aux équipes autorisées de {c['name']} et à nos sous-traitants techniques (hébergement Scalingo, paiements Stripe, email SMTP le cas échéant), dans le respect du RGPD.</p>

<h2>6. Transferts hors UE</h2>
<p>Certains prestataires (ex. Stripe, Mistral AI pour l'assistant) peuvent traiter des données hors Union européenne. Des garanties appropriées (clauses contractuelles types) sont mises en place le cas échéant.</p>

<h2>7. Vos droits</h2>
<p>Vous disposez des droits d'accès, rectification, effacement, limitation, opposition et portabilité. Pour les exercer : <a href="mailto:{c['email']}">{c['email']}</a>.</p>
<p>Vous pouvez introduire une réclamation auprès de la CNIL (<a href="https://www.cnil.fr" rel="noopener noreferrer" target="_blank">www.cnil.fr</a>).</p>

<h2>8. Cookies</h2>
<p>Consultez notre <a href="/cookies">politique cookies</a> pour gérer vos préférences.</p>
"""


def _en_privacy() -> str:
    c = LEGAL_COMPANY
    return f"""
<p><em>Last updated: June 2026</em></p>

<p>{c['name']} (French SARL, SIREN {c['siren']}) operates the Iotplace B2B IoT marketplace. This policy explains how we process personal data under the GDPR.</p>

<h2>1. Data controller</h2>
<p>{c['name']} — {c['rcs']}<br>Email: <a href="mailto:{c['email']}">{c['email']}</a></p>

<h2>2. Data we collect</h2>
<ul>
  <li><strong>Contact form</strong>: name, email, country, profile type, message.</li>
  <li><strong>User accounts</strong>: identity, professional details, enterprise or startup profile.</li>
  <li><strong>Browsing</strong>: pages visited, session duration (only if you accept analytics cookies).</li>
  <li><strong>Payments</strong>: processed by Stripe (we do not store card details).</li>
</ul>

<h2>3. Purposes and legal bases</h2>
<ul>
  <li>Respond to enquiries — legitimate interest / pre-contractual steps.</li>
  <li>Account and mission management — contract performance.</li>
  <li>Site improvement — consent (analytics cookies).</li>
  <li>Legal and accounting obligations — legal obligation.</li>
</ul>

<h2>4. Retention</h2>
<ul>
  <li>Contact messages: 3 years from last exchange.</li>
  <li>Active accounts: contract duration + 5 years.</li>
  <li>Analytics data: 13 months maximum.</li>
</ul>

<h2>5. Recipients</h2>
<p>Authorised {c['name']} staff and technical processors (Scalingo hosting, Stripe payments, SMTP email when configured), under GDPR safeguards.</p>

<h2>6. International transfers</h2>
<p>Some providers (e.g. Stripe, Mistral AI) may process data outside the EU with appropriate safeguards.</p>

<h2>7. Your rights</h2>
<p>Access, rectification, erasure, restriction, objection and portability: <a href="mailto:{c['email']}">{c['email']}</a>.</p>
<p>You may lodge a complaint with your supervisory authority.</p>

<h2>8. Cookies</h2>
<p>See our <a href="/cookies">cookie policy</a> to manage preferences.</p>
"""


def _fr_cookies() -> str:
    return """
<p><em>Dernière mise à jour : juin 2026</em></p>

<p>Ce site utilise des cookies et technologies similaires. Vous pouvez accepter ou refuser les cookies non essentiels via le bandeau affiché lors de votre première visite, ou modifier vos choix à tout moment en cliquant sur « Gérer les cookies » en bas de page.</p>

<h2>1. Cookies strictement nécessaires</h2>
<p>Ces cookies sont indispensables au fonctionnement du site. Ils ne nécessitent pas votre consentement.</p>
<table class="legal-table">
  <thead><tr><th>Nom</th><th>Finalité</th><th>Durée</th></tr></thead>
  <tbody>
    <tr><td><code>session</code></td><td>Session Flask : authentification, langue, sécurité CSRF</td><td>Session (8 h max)</td></tr>
    <tr><td><code>iot_consent</code></td><td>Mémorise vos choix de consentement cookies</td><td>13 mois</td></tr>
  </tbody>
</table>

<h2>2. Cookies analytiques (avec consentement)</h2>
<p>Activés uniquement si vous cliquez sur « Tout accepter » ou activez l'option analytique.</p>
<table class="legal-table">
  <thead><tr><th>Nom</th><th>Finalité</th><th>Durée</th></tr></thead>
  <tbody>
    <tr><td><code>iot_sid</code> (sessionStorage)</td><td>Identifiant de session pour mesurer les pages vues (analytics interne)</td><td>Session navigateur</td></tr>
    <tr><td><code>_ga</code>, <code>_gid</code></td><td>Google Analytics (si configuré par l'administrateur)</td><td>13 mois / 24 h</td></tr>
  </tbody>
</table>

<h2>3. Gérer vos préférences</h2>
<p>Utilisez le lien <strong>Gérer les cookies</strong> en pied de page, ou supprimez les cookies via les paramètres de votre navigateur.</p>

<h2>4. En savoir plus</h2>
<p>Consultez notre <a href="/politique-de-confidentialite">politique de confidentialité</a> pour le traitement des données personnelles.</p>
"""


def _en_cookies() -> str:
    return """
<p><em>Last updated: June 2026</em></p>

<p>This site uses cookies and similar technologies. You can accept or reject non-essential cookies via the banner on first visit, or change your choices anytime using <strong>Manage cookies</strong> in the footer.</p>

<h2>1. Strictly necessary cookies</h2>
<p>Required for the site to work. No consent needed.</p>
<table class="legal-table">
  <thead><tr><th>Name</th><th>Purpose</th><th>Duration</th></tr></thead>
  <tbody>
    <tr><td><code>session</code></td><td>Flask session: auth, language, CSRF</td><td>Session (8 h max)</td></tr>
    <tr><td><code>iot_consent</code></td><td>Stores your cookie consent choices</td><td>13 months</td></tr>
  </tbody>
</table>

<h2>2. Analytics cookies (with consent)</h2>
<p>Enabled only if you click <strong>Accept all</strong> or enable analytics.</p>
<table class="legal-table">
  <thead><tr><th>Name</th><th>Purpose</th><th>Duration</th></tr></thead>
  <tbody>
    <tr><td><code>iot_sid</code> (sessionStorage)</td><td>Session ID for first-party page analytics</td><td>Browser session</td></tr>
    <tr><td><code>_ga</code>, <code>_gid</code></td><td>Google Analytics (if configured)</td><td>13 months / 24 h</td></tr>
  </tbody>
</table>

<h2>3. Manage preferences</h2>
<p>Use <strong>Manage cookies</strong> in the footer, or clear cookies in your browser settings.</p>

<h2>4. More information</h2>
<p>See our <a href="/privacy">privacy policy</a> for personal data processing.</p>
"""


def _fr_terms() -> str:
    c = LEGAL_COMPANY
    court_city = c["rcs"].split(" R.C.S. ")[-1] if " R.C.S. " in c["rcs"] else "Nanterre"
    return f"""
<p><em>Dernière mise à jour : juin 2026</em></p>

<p>Les présentes Conditions Générales d'Utilisation et de Vente (« CGU/CGV ») régissent l'accès et l'utilisation de la plateforme Iotplace, éditée par {c['name']} ({c['form']}), {c['rcs']}, ainsi que les prestations de mise en relation et de paiement qu'elle propose. Toute inscription vaut acceptation pleine et entière des présentes.</p>

<h2>1. Objet</h2>
<p>Iotplace est une marketplace B2B de sous-traitance IoT mettant en relation des <strong>entreprises</strong> (donneurs d'ordre) et des <strong>startups</strong> (prestataires) pour des missions de développement firmware, hardware, cloud et intégration. Iotplace agit en qualité d'<strong>intermédiaire technique</strong> et n'est pas partie au contrat de prestation conclu entre l'entreprise et la startup.</p>

<h2>2. Définitions</h2>
<ul>
  <li><strong>Membre</strong> : toute entreprise ou startup disposant d'un compte.</li>
  <li><strong>Mission</strong> : prestation IoT publiée par une entreprise et réalisée par une startup.</li>
  <li><strong>Séquestre (escrow)</strong> : conservation des fonds par le prestataire de paiement jusqu'à validation de la mission.</li>
  <li><strong>Commission</strong> : rémunération d'Iotplace prélevée sur les missions réalisées via la plateforme.</li>
</ul>

<h2>3. Inscription et compte</h2>
<p>L'inscription est gratuite et réservée aux professionnels. Le Membre garantit l'exactitude des informations fournies et la confidentialité de ses identifiants. Iotplace peut suspendre ou supprimer tout compte en cas de manquement aux présentes, de fraude ou d'usage illicite.</p>

<h2>4. Rôle et obligations d'Iotplace</h2>
<p>Iotplace fournit l'outil de mise en relation, de messagerie, de suivi et de paiement sécurisé. Iotplace ne garantit ni la conclusion d'une mission, ni la qualité des prestations, ni la solvabilité des Membres. Iotplace met en œuvre des moyens raisonnables pour assurer la disponibilité du service, sans obligation de résultat.</p>

<h2>5. Obligations des Membres</h2>
<p>Les entreprises s'engagent à décrire leurs besoins de bonne foi et à régler les sommes dues. Les startups s'engagent à ne candidater que sur des missions qu'elles sont en mesure de réaliser et à livrer conformément à ce qui est convenu. Chaque Membre reste seul responsable du respect de ses obligations légales, fiscales et réglementaires.</p>

<h2>6. Conditions financières</h2>
<ul>
  <li><strong>Inscription et publication</strong> : gratuites.</li>
  <li><strong>Commission</strong> : un pourcentage de chaque mission réalisée est prélevé par Iotplace (taux indiqué sur la <a href="/pricing">page Tarifs</a>, réduit pour les comptes Pro).</li>
  <li><strong>Frais de candidature PoC</strong> : la candidature à un projet en phase PoC peut être soumise à des frais fixes indiqués avant paiement.</li>
  <li><strong>Abonnement Pro</strong> : option mensuelle offrant projets illimités, commission réduite et matching prioritaire.</li>
</ul>
<p>Les montants sont exprimés hors taxes ; la TVA applicable est ajoutée le cas échéant.</p>

<h2>7. Paiement et séquestre</h2>
<p>Les paiements sont opérés via notre prestataire <strong>Stripe</strong> (Stripe Payments Europe). À l'acceptation d'une candidature, une facture est émise à l'entreprise et les fonds sont conservés en <strong>séquestre</strong>. Après validation de la mission par l'entreprise, Iotplace libère la part due à la startup via Stripe Connect, déduction faite de la commission. L'utilisation des services de paiement implique l'acceptation des conditions de Stripe.</p>

<h2>8. Propriété intellectuelle</h2>
<p>Sauf accord contraire entre l'entreprise et la startup, les livrables d'une mission sont régis par le contrat conclu entre elles. La marque, le code et les contenus d'Iotplace demeurent la propriété exclusive de {c['name']}.</p>

<h2>9. Responsabilité</h2>
<p>Iotplace ne saurait être tenue responsable des litiges, retards, manquements ou dommages liés à l'exécution des missions entre Membres. La responsabilité d'Iotplace, lorsqu'elle est engagée, est limitée au montant des commissions perçues sur la mission concernée.</p>

<h2>10. Données personnelles</h2>
<p>Le traitement des données est décrit dans notre <a href="/politique-de-confidentialite">politique de confidentialité</a> et notre <a href="/cookies">politique cookies</a>.</p>

<h2>11. Durée, résiliation</h2>
<p>Les présentes s'appliquent pendant toute la durée d'utilisation du service. Le Membre peut fermer son compte à tout moment ; les missions et paiements en cours restent régis par les présentes jusqu'à leur terme.</p>

<h2>12. Droit applicable</h2>
<p>Les présentes sont soumises au droit français. À défaut de résolution amiable, tout litige relève de la compétence des tribunaux du ressort de {court_city}.</p>

<h2>13. Contact</h2>
<p>Pour toute question relative aux présentes : <a href="mailto:{c['email']}">{c['email']}</a>.</p>
"""


def _en_terms() -> str:
    c = LEGAL_COMPANY
    return f"""
<p><em>Last updated: June 2026</em></p>

<p>These Terms of Use and Sale (the "Terms") govern access to and use of the Iotplace platform, published by {c['name']} ({c['form']}), {c['rcs']}, as well as the matchmaking and payment services it provides. Creating an account constitutes full acceptance of these Terms.</p>

<h2>1. Purpose</h2>
<p>Iotplace is a B2B IoT subcontracting marketplace connecting <strong>enterprises</strong> (clients) with <strong>startups</strong> (providers) for firmware, hardware, cloud and integration missions. Iotplace acts as a <strong>technical intermediary</strong> and is not a party to the service contract concluded between the enterprise and the startup.</p>

<h2>2. Definitions</h2>
<ul>
  <li><strong>Member</strong>: any enterprise or startup holding an account.</li>
  <li><strong>Mission</strong>: an IoT engagement published by an enterprise and delivered by a startup.</li>
  <li><strong>Escrow</strong>: funds held by the payment provider until the mission is validated.</li>
  <li><strong>Commission</strong>: Iotplace's fee charged on missions carried out via the platform.</li>
</ul>

<h2>3. Registration and account</h2>
<p>Registration is free and reserved for professionals. The Member warrants the accuracy of the information provided and the confidentiality of its credentials. Iotplace may suspend or delete any account in case of breach, fraud or unlawful use.</p>

<h2>4. Iotplace's role and obligations</h2>
<p>Iotplace provides the matchmaking, messaging, tracking and secure payment tools. Iotplace does not guarantee that a mission will be concluded, the quality of the services, or the solvency of Members. Iotplace uses reasonable means to keep the service available, with no obligation of result.</p>

<h2>5. Members' obligations</h2>
<p>Enterprises undertake to describe their needs in good faith and to pay the amounts due. Startups undertake to apply only to missions they are able to deliver and to deliver as agreed. Each Member remains solely responsible for compliance with its legal, tax and regulatory obligations.</p>

<h2>6. Financial terms</h2>
<ul>
  <li><strong>Registration and posting</strong>: free.</li>
  <li><strong>Commission</strong>: a percentage of each completed mission is charged by Iotplace (rate shown on the <a href="/pricing">Pricing page</a>, reduced for Pro accounts).</li>
  <li><strong>PoC application fee</strong>: applying to a PoC-phase project may be subject to a fixed fee shown before payment.</li>
  <li><strong>Pro subscription</strong>: an optional monthly plan offering unlimited projects, a reduced commission and priority matching.</li>
</ul>
<p>Amounts are stated excluding tax; applicable VAT is added where relevant.</p>

<h2>7. Payment and escrow</h2>
<p>Payments are processed through our provider <strong>Stripe</strong> (Stripe Payments Europe). When an application is accepted, an invoice is issued to the enterprise and the funds are held in <strong>escrow</strong>. After the enterprise validates the mission, Iotplace releases the startup's share via Stripe Connect, net of commission. Using the payment services implies acceptance of Stripe's terms.</p>

<h2>8. Intellectual property</h2>
<p>Unless otherwise agreed between the enterprise and the startup, mission deliverables are governed by the contract concluded between them. Iotplace's brand, code and content remain the exclusive property of {c['name']}.</p>

<h2>9. Liability</h2>
<p>Iotplace shall not be liable for disputes, delays, breaches or damages arising from the performance of missions between Members. Where engaged, Iotplace's liability is limited to the amount of commissions collected on the mission concerned.</p>

<h2>10. Personal data</h2>
<p>Data processing is described in our <a href="/privacy">privacy policy</a> and <a href="/cookies">cookie policy</a>.</p>

<h2>11. Term and termination</h2>
<p>These Terms apply throughout the use of the service. A Member may close its account at any time; ongoing missions and payments remain governed by these Terms until completion.</p>

<h2>12. Governing law</h2>
<p>These Terms are governed by French law. Failing an amicable settlement, any dispute falls under the jurisdiction of the competent courts at the publisher's registered office.</p>

<h2>13. Contact</h2>
<p>For any question regarding these Terms: <a href="mailto:{c['email']}">{c['email']}</a>.</p>
"""


def get_legal_body(slug: str, locale: str = "fr") -> str:
    bodies = {
        ("legal", "fr"): _fr_mentions,
        ("legal", "en"): _en_legal,
        ("privacy", "fr"): _fr_privacy,
        ("privacy", "en"): _en_privacy,
        ("cookies", "fr"): _fr_cookies,
        ("cookies", "en"): _en_cookies,
        ("terms", "fr"): _fr_terms,
        ("terms", "en"): _en_terms,
    }
    factory = bodies.get((slug, locale)) or bodies.get((slug, "fr"))
    return factory() if factory else ""
