# SGI-GP - Architecture Technique

## 1. Vue d'Ensemble

L'application **SGI-GP (Système de Gestion Intégrée - GoPass)** est une plateforme monolithique modulaire basée sur le framework **Flask**. Elle est conçue pour gérer l'émission, la vente et le contrôle sécurisé de titres de transport aéroportuaires ("GoPass") en environnement contraint (faible connectivité, haute sécurité).

### Principes Clés
*   **Modularité :** Utilisation de `Blueprints` Flask pour séparer les domaines métier (Auth, Public, API, Ops, Admin).
*   **Sécurité par Design :** Validation stricte des entrées, protection CSRF globale, et headers de sécurité HTTP (HSTS, CSP).
*   **Performance :** Génération de PDF en mémoire (in-memory buffers), requêtes SQL optimisées (`joinedload`), et chargement asynchrone des assets.

---

## 2. Stack Technologique

### Backend
*   **Langage :** Python 3.10+
*   **Framework Web :** Flask 3.0.0
*   **Serveur d'Application (WSGI) :** Gunicorn 21.2.0
*   **ORM :** SQLAlchemy 2.0 (via Flask-SQLAlchemy 3.1.1)
*   **Authentification :** Flask-Login 0.6.3 (Sessions serveur sécurisées)
*   **Traitement PDF :** ReportLab 4.0 (Génération vectorielle haute performance)
*   **Tâches de Fond :** `threading` (pour la synchro API et l'envoi d'emails simples), `asgiref` (pour les appels asynchrones).

### Frontend
*   **Moteur de Template :** Jinja2 (Rendu côté serveur pour SEO et Sécurité).
*   **CSS Framework :** Tailwind CSS (Utility-first).
*   **JavaScript :** ES6+ Vanilla (Pas de framework lourd type React/Vue).
    *   **Librairies JS :** `Chart.js` (Dashboard), `html5-qrcode` (Scanner Web).
*   **Design :** Mobile-First (Responsive pour PDA et Smartphones).

### Base de Données
*   **Production :** PostgreSQL 13+ (`psycopg2-binary`).
*   **Développement :** SQLite (pour la rapidité de prototypage).
*   **Schéma :** Relationnel strict avec contraintes d'intégrité (Foreign Keys).

### Intégrations Externes
*   **Vols :** AviationStack API (REST/JSON).
*   **Paiement :** Stripe (PaymentIntent API), APIs Mobile Money locales (Simulées ou via agrégateur).
*   **Export :** OpenPyXL (Génération Excel native).

---

## 3. Structure du Projet

```bash
/
├── app.py                 # Point d'entrée (Application Factory)
├── config/                # Configuration (Env Vars, Logging)
├── models/                # Modèles de Données (SQLAlchemy)
│   └── __init__.py        # Définition des tables (User, GoPass, Flight...)
├── routes/                # Contrôleurs (Blueprints)
│   ├── api.py             # API REST (Mobile/POS)
│   ├── auth.py            # Authentification
│   ├── ops.py             # Opérations Terrain (Scanner, POS)
│   ├── public.py          # E-Commerce (Achat Web)
│   ├── dashboard.py       # Administration
│   └── ...
├── services/              # Logique Métier (Service Layer)
│   ├── gopass_service.py  # Cœur du système (PDF, Validation)
│   ├── flight_service.py  # Gestion des Vols & Sync
│   └── external_data_sync.py # Connecteurs API
├── statics/               # Assets (JS, CSS, Images)
├── templates/             # Vues HTML (Jinja2)
├── tests/                 # Tests unitaires et d'intégration
└── docs/                  # Documentation (Vous êtes ici)
```

---

## 4. Modèle de Données (Schema)

Le schéma de base de données est centré sur l'entité `GoPass` et sa relation indissociable avec un `Flight` ("Flight-Bound").

### Entités Principales

1.  **`User` (Utilisateurs)**
    *   `role` : Définit les permissions (`admin`, `agent`, `controller`, `holder`).
    *   `location` : Code aéroport d'affectation (ex: 'FIH').
    *   `password_hash` : Stockage sécurisé (Argon2/PBKDF2).

2.  **`Flight` (Vols)**
    *   `flight_number` : Identifiant commercial (ex: AF123).
    *   `departure_time` : Date/Heure UTC.
    *   `status` : État du vol (`scheduled`, `active`, `landed`, `closed`).
    *   **Source :** `manual` (Saisie locale) ou `api` (AviationStack).

3.  **`GoPass` (Titres de Transport)**
    *   **Clé Étrangère :** `flight_id` (Lien fort).
    *   `token` : Hash SHA-256 unique pour la validation QR.
    *   `status` : État du billet (`valid`, `consumed`, `expired`).
    *   `passenger_name` : Donnée nominative (Anti-revente).

4.  **`Transaction` (Finances)**
    *   Trace chaque flux financier (Vente Cash, Stripe, MM).
    *   Liée à un `agent` (si vente guichet) ou `null` (si vente web).

5.  **`AccessLog` (Traçabilité)**
    *   Enregistre **chaque** tentative de scan (Succès ou Échec).
    *   Champs : `validator_id`, `timestamp`, `result_code` (A, B, C, D), `location`.

---

## 5. Sécurité & Flux de Données

### 5.1 Sécurisation des Billets
L'intégrité du billet repose sur la signature cryptographique contenue dans le QR Code.
*   **Génération :** `Token = HMAC-SHA256(Flight_ID + Passport + Timestamp + Secret_Key)`.
*   **Validation :** Le scanner envoie le token brut. Le serveur vérifie sa correspondance exacte en base.
*   **Anti-Rejeu :** Un token scanné passe immédiatement à l'état `consumed`. Toute tentative ultérieure déclenche une alerte de sécurité ("Double Scan").

### 5.2 Protection de l'Infrastructure
*   **Base de Données :** En Production, l'accès direct est interdit. L'application utilise un pool de connexions géré par SQLAlchemy.
*   **Sessions :** Les cookies de session sont signés cryptographiquement pour empêcher la falsification de l'identité utilisateur.
*   **Uploads :** Les fichiers (Logos, Manifestes) sont validés par extension et type MIME avant stockage. Les noms de fichiers sont aseptisés (`secure_filename`).

### 5.3 Conformité
*   **RGPD / Données Personnelles :** Les données passagers sont conservées uniquement pour la durée légale de traçabilité (configurable), puis anonymisées ou archivées.
*   **PCI-DSS :** Aucune donnée de carte bancaire ne transite par les serveurs SGI-GP. Tout est délégué à Stripe via `Stripe.js` (Tokenisation client-side).
