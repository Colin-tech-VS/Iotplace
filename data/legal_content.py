"""Default legal page bodies (FR / EN) — editable via CRM."""

LEGAL_COMPANY = {
    "name": "Iotplace",
    "form": "SARL, société à responsabilité limitée",
    "siren": "980 867 485",
    "siret": "980 867 485 00016",
    "vat": "FR88980867485",
    "rcs": "980 867 485 R.C.S. Nanterre",
    "rcs_date": "26/10/2023",
    "email": "hello@iotplace.io",
    "host": "Scalingo SAS",
    "host_address": "13 rue de la Tour des Dames, 75009 Paris, France",
    "host_site": "https://scalingo.com",
}


def _fr_mentions() -> str:
    c = LEGAL_COMPANY
    return f"""
<h2>1. Éditeur du site</h2>
<p>Le site <strong>iotplace.io</strong> est édité par :</p>
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
<p>The website <strong>iotplace.io</strong> is published by:</p>
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


def get_legal_body(slug: str, locale: str = "fr") -> str:
    bodies = {
        ("legal", "fr"): _fr_mentions,
        ("legal", "en"): _en_legal,
        ("privacy", "fr"): _fr_privacy,
        ("privacy", "en"): _en_privacy,
        ("cookies", "fr"): _fr_cookies,
        ("cookies", "en"): _en_cookies,
    }
    factory = bodies.get((slug, locale)) or bodies.get((slug, "fr"))
    return factory() if factory else ""
