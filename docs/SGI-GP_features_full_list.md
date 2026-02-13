# SGI-GP - Bible des Fonctionnalités

Ce document recense l'intégralité des fonctionnalités techniques et métier de la plateforme SGI-GP (Système de Gestion Intégrée - GoPass). Chaque fonctionnalité est décrite avec ses règles de validation, ses comportements attendus et ses impacts système.

## 1. Cœur du Système : Le GoPass (Billet)

### 1.1 Génération de Billet
*   **Identifiant Unique (Token) :** Chaque billet possède un `token` unique généré via un hachage SHA-256 d'un JSON contenant `{vol_id, passeport, timestamp, nonce}`. Ce token est signé numériquement pour garantir l'authenticité.
*   **QR Code :** Le token est encodé dans un QR Code (Version 1, Correction M) généré à la volée en mémoire (pas de stockage disque) via la librairie `qrcode[pil]`.
*   **Principe "Flight-Bound" :** Un billet est strictement lié à un `flight_id` unique. Il n'est pas transférable sur un autre vol ni une autre date.

### 1.2 Formats d'Impression (PDF)
Le système génère des PDF via `ReportLab` avec gestion optimisée des assets (chargement unique des logos en mémoire).
*   **Format A4 (E-GoPass / Web) :**
    *   Orientation Paysage.
    *   Double exemplaire (Client / Souche) ou exemplaire unique selon configuration.
    *   Contient : Détails du vol, Nom du passager, QR Code de sécurité, Mentions légales.
*   **Format Thermique (POS / Guichet) :**
    *   Largeur : 80mm.
    *   Design compact "Ticket de Caisse".
    *   Optimisé pour imprimantes thermiques (EPSON TM-T88 ou compatible).
    *   Contient : Logo RVA, Détails Vol (Gras), QR Code centré, ID Agent vendeur, Référence Transaction.

### 1.3 Cycle de Vie (Statuts)
*   `valid` : Billet payé et émis, prêt à être scanné.
*   `consumed` : Billet scanné avec succès à l'embarquement.
*   `expired` : Billet non utilisé après la date du vol.
*   `cancelled` : Billet annulé par un administrateur (remboursement).

---

## 2. Authentification & Sécurité

### 2.1 Gestion des Utilisateurs
*   **Modèle RBAC (Role-Based Access Control) :**
    *   `admin` : Accès total (Configuration, Rapports financiers, Gestion utilisateurs).
    *   `agent` : Vente (POS), Upload Manifeste, Clôture de caisse.
    *   `controller` : Accès uniquement au module Scanner (Validation).
    *   `holder` : Passager (Accès limité à ses propres billets - *Feature Web*).
*   **Sécurité des Mots de Passe :** Hachage via `Werkzeug` (PBKDF2-SHA256).

### 2.2 Sécurité Applicative
*   **Protection CSRF :** `Flask-WTF` protège tous les formulaires POST contre les attaques Cross-Site Request Forgery.
*   **En-têtes HTTP (Security Headers) :**
    *   `Strict-Transport-Security` (HSTS) : Force HTTPS.
    *   `Content-Security-Policy` (CSP) : Bloque les scripts tiers non autorisés.
    *   `X-Frame-Options` : Empêche le Clickjacking (DENY/SAMEORIGIN).
*   **Session Management :** Cookies `HttpOnly`, `Secure` (en prod), et `SameSite=Lax`.

---

## 3. Gestion des Vols

### 3.1 Synchronisation Externe (API)
*   **Source :** AviationStack API.
*   **Fréquence :** Manuelle (bouton Sync) ou Planifiée (Cron).
*   **Données Récupérées :** Numéro de vol, Horaires (Départ/Arrivée), Statut (Scheduled, Landed, Cancelled), Aéroport de destination.
*   **Filtrage :** Seuls les vols au départ des aéroports configurés (ex: FIH, FBM) sont importés.

### 3.2 Vols Manuels (Mode Dégradé / Brousse)
*   Permet la création de vols pour les compagnies non listées dans l'API ou les petits aérodromes.
*   **Champs obligatoires :** Numéro de Vol, Compagnie, Heure Départ, Destination.
*   **Validation :** Unicité du numéro de vol pour la journée en cours.

### 3.3 Audit des Manifestes (Anti-Coulage)
*   **Upload :** L'agent charge le fichier (Excel/PDF) fourni par la compagnie après clôture du vol.
*   **Comparaison Automatique :** Le système compare le `manifest_pax_count` (déclaré) avec le nombre de `GoPass` scannés (`consumed`) pour ce vol.
*   **Alerte :** Tout écart négatif (Déclaré < Scannés) génère une alerte de fraude potentielle.

---

## 4. Vente & Paiement (POS / Web)

### 4.1 Point de Vente (POS) - Guichet
*   **Flux Rapide :** Sélection Vol -> Saisie Pax -> Paiement Cash -> Impression Thermique.
*   **Calcul Automatique du Prix :** Basé sur la configuration `Tariff` (National/International, Adulte/Enfant).
*   **Gestion de Caisse (Cash Drop) :**
    *   L'agent doit déclarer le montant de son encaisse en fin de shift.
    *   Validation par un Superviseur (Double Check).
    *   Traçabilité : Chaque billet vendu est lié à l'ID de l'agent (`sold_by`).

### 4.2 Vente en Ligne (Web)
*   **Paiement Électronique :**
    *   **Stripe :** Intégration via `PaymentIntent` (SCA Compliant). Webhook pour confirmation asynchrone.
    *   **Mobile Money :** (M-Pesa, Orange Money, Airtel) via intégration API locale (Logs de réconciliation).
*   **Délivrance :** Envoi automatique du PDF par email après confirmation du paiement.

---

## 5. Module Scanner (Contrôle)

### 5.1 Algorithme de Validation (Logique A/B/C/D)
Le scanner analyse le QR Code et retourne un statut visuel immédiat :

1.  **Code A - VERT (VALIDE) :**
    *   *Condition :* Billet existant, statut `valid`, `flight_id` correspond au vol scanné.
    *   *Action :* Mise à jour atomique du statut vers `consumed`, enregistrement `AccessLog`.
2.  **Code B - ROUGE (DÉJÀ SCANNÉ) :**
    *   *Condition :* Billet existant, statut `consumed`.
    *   *Action :* Affiche l'heure et l'agent du premier scan (Preuve de fraude).
3.  **Code C - ORANGE (MAUVAIS VOL) :**
    *   *Condition :* Billet valide mais `flight_id` différent du vol scanné.
    *   *Action :* Affiche le vol pour lequel le billet est valide. Bloque l'accès.
4.  **Code D - ROUGE (INVALIDE/EXPIRÉ) :**
    *   *Condition :* Token inconnu, signature invalide, ou date de vol passée.
    *   *Action :* Rejet total.

### 5.2 Fonctionnalités Avancées Scanner
*   **Mode Offline (Dégradé) :** Capacité de valider la signature cryptographique localement si le serveur est injoignable (nécessite la clé publique sur le terminal). Synchronisation différée des logs.
*   **Statistiques Temps Réel :** Affichage du nombre de passagers embarqués vs capacité du vol sur le terminal.

---

## 6. Administration & Reporting

### 6.1 Tableau de Bord (Dashboard)
*   **KPIs :** Ventes du jour, Chiffre d'affaires global, Taux de remplissage.
*   **Graphiques :** Évolution des ventes (Chart.js), Répartition par compagnie.

### 6.2 Configuration Dynamique (Settings)
*   **Gestion des Tarifs :** CRUD sur les prix par type de vol et catégorie passager.
*   **Personnalisation :** Upload des logos (RVA, GoPass) via l'interface admin (stockage statique).
*   **Toggles :** Activation/Désactivation des modes de paiement (Stripe, Mobile Money) à chaud.

### 6.3 Logs & Audit
*   **AccessLog :** Historique complet de chaque scan (Qui, Quand, Où, Résultat).
*   **Transaction Logs :** Piste d'audit financière pour chaque centime encaissé.
