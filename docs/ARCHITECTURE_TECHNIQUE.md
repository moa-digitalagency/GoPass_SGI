# ARCHITECTURE TECHNIQUE

## 1. Stack Technique

### Backend
*   **Langage :** Python 3.x
*   **Framework :** Flask 3.0.0
*   **Serveur WSGI :** Gunicorn
*   **ORM :** SQLAlchemy (Flask-SQLAlchemy)
*   **Authentification :** Flask-Login (Sessions serveur)
*   **PDF Generation :** ReportLab
*   **Excel Parsing :** OpenPyXL
*   **External APIs :** Requests (AviationStack)

### Frontend
*   **Templates :** Jinja2 (Rendu côté serveur)
*   **CSS :** Tailwind CSS (via CDN ou build statique)
*   **JavaScript :** ES6+ (Logique scanner, graphiques Chart.js)

### Base de Données
*   **Moteur Dev :** SQLite
*   **Moteur Prod :** PostgreSQL (`psycopg2-binary`)
*   **Migrations :** Gestion manuelle via `init_db.py` (vérification de schéma au démarrage)

## 2. Structure du Projet

```
/
├── app.py                 # Point d'entrée de l'application (Factory pattern)
├── config.py              # Configuration par environnement
├── init_db.py             # Script d'initialisation et seeding DB
├── requirements.txt       # Dépendances Python
├── models/                # Définitions des tables (SQLAlchemy)
│   └── __init__.py        # Tous les modèles (User, GoPass, Flight, etc.)
├── routes/                # Contrôleurs (Blueprints)
│   ├── api.py             # Endpoints API REST
│   ├── auth.py            # Login/Logout
│   ├── ops.py             # Opérations Terrain (POS, Scanner)
│   ├── public.py          # Parcours Grand Public (Achat Web)
│   ├── finance.py         # Gestion Trésorerie
│   └── ...
├── services/              # Logique Métier (Service Layer)
│   ├── gopass_service.py  # Cœur du système (Création, Validation)
│   ├── flight_service.py  # Gestion Vols & API
│   └── finance_service.py # Calculs financiers & Réconciliation
├── statics/               # Assets (CSS, JS, Images, Uploads)
├── templates/             # Vues HTML (Jinja2)
└── docs/                  # Documentation technique
```

## 3. Schéma de Base de Données (ERD Simplifié)

Les tables clés et leurs relations :

*   **`User`** : Agents, Admins, Contrôleurs.
    *   `role` : 'admin', 'agent', 'controller', 'holder'.
    *   `location` : Code aéroport (ex: 'FIH').
*   **`Flight`** : Vols.
    *   `flight_number`, `date`, `status` ('scheduled', 'closed'...).
    *   `manifest_pax_count` : Déclaré par la compagnie (Audit).
*   **`GoPass`** : Le billet (Ticket).
    *   FK `flight_id` (Lien Flight-Bound).
    *   `token` : Hash unique pour QR Code.
    *   `status` : 'valid', 'consumed', 'expired'.
*   **`Transaction`** : Flux financier.
    *   FK `agent_id`.
    *   `payment_method` (Cash, Mobile Money).
*   **`AccessLog`** : Traçabilité des scans.
    *   FK `pass_id`, `validator_id`.
    *   `status` : 'VALID', 'ALREADY_SCANNED', 'WRONG_FLIGHT'.
*   **`FlightManifest`** : Fichiers manifestes uploadés pour audit.
*   **`AppConfig`** : Configuration dynamique de l'application (clé-valeur).
    *   Stocke les URLs des logos, le nom du site, les prix IDEF, etc.
    *   Permet aux Super Admins de modifier les paramètres sans redéploiement.

## 4. Sécurité

### Authentification & Rôles (RBAC)
*   Utilisation de `Flask-Login` avec décorateurs `@role_required` et `@agent_required`.
*   Mots de passe hashés via `Werkzeug` (PBKDF2/SHA256).

### Signature QR Code (Flight-Bound)
*   **Format :** JSON contenant `{id_billet, vol, date, hash_signature}`.
*   **Intégrité :** Le `token` stocké en base est un hash SHA256 des données critiques + nonce.
*   **Validation :** Le scanner envoie le token; le serveur vérifie l'existence et l'état dans la table `GoPass`.

### Sécurisation des Paiements
*   **Cash :** Suivi par agent (`sold_by`) et dépôt via `CashDeposit`.
*   **Mobile Money :** Logs bruts dans `MobileMoneyLog` pour réconciliation asynchrone.
*   **Stripe :** Intégration via `PaymentGateway` (activable/désactivable).

## 5. Flux de Données

### 1. Vente (POS / Web)
1.  **Frontend :** Formulaire passager + Sélection Vol.
2.  **Route :** `POST /ops/pos/sale` ou `POST /checkout`.
3.  **Service :** `GoPassService.create_gopass()`
    *   Vérifie le vol.
    *   Génère le hash/token.
    *   Crée l'enregistrement `GoPass` (statut 'valid').
    *   Si POS : Associe la vente à l'agent connecté.
4.  **Sortie :** Génération PDF (Thermal ou A4) via `ReportLab`.

### 2. Contrôle (Scanner)
1.  **Frontend :** Caméra JS scanne le QR.
2.  **API :** Envoi du token à `GoPassService.validate_gopass()`.
3.  **Logique :**
    *   Vérifie existence token.
    *   Vérifie statut vol (`closed` ?).
    *   Vérifie correspondance vol (`flight_id`).
    *   Vérifie état billet (`consumed` ?).
4.  **DB :** Création d'un `AccessLog` (Succès ou Échec).
5.  **Mise à jour :** Si valide, `GoPass.status` passe à 'consumed'.
