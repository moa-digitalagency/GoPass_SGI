# STRATÉGIE MÉTIER & RÈGLES DE GESTION

Ce document détaille les choix d'implémentation répondant aux exigences du cahier des charges SGI-GP, axés sur la sécurisation des recettes et la traçabilité.

## 1. Principe "Flight-Bound" (Liaison Vol Unique)

### Concept
Contrairement à un système de "crédit" ou de "portefeuille", chaque GoPass est strictement lié à un vol spécifique à une date précise.
**Règle :** `1 Billet = 1 Vol = 1 Date`.

### Implémentation Technique
*   **Modèle de Données :** La table `GoPass` contient une clé étrangère `flight_id` non nulle.
*   **Validation (Scanner) :**
    *   Lors du scan, le système compare l'`id` du vol programmé dans le scanner avec le `flight_id` du billet.
    *   **Cas C (Orange) :** Si les IDs diffèrent, le scanner retourne une alerte "MAUVAIS VOL" même si le billet est valide par ailleurs.
    *   **Objectif :** Empêcher l'utilisation d'un billet valide sur un autre vol (ex: un billet pour le vol de 10h utilisé sur celui de 14h), ce qui fausserait les manifestes.

## 2. Maximisation des Recettes & Anti-Fraude

### Sécurisation du Cash (Guichet)
*   **Problème :** Risque de non-reversement des espèces par les agents percepteurs.
*   **Solution :**
    *   Chaque vente est enregistrée avec l'ID de l'agent (`sold_by`).
    *   Un "Total Théorique" est calculé en temps réel.
    *   Le module `Finance` oblige l'agent à déclarer son encaisse (`CashDeposit`).
    *   Tout écart entre le théorique et le déclaré est signalé.

### Réconciliation Mobile Money
*   **Problème :** Les callbacks de paiement (M-Pesa, Orange Money) peuvent échouer ou être falsifiés.
*   **Solution :**
    *   **Double Entrée :**
        1.  La table `GoPass` stocke le statut de paiement du ticket.
        2.  La table `MobileMoneyLog` stocke les notifications brutes du fournisseur.
    *   **Algorithme de Réconciliation :** Un processus (batch ou à la demande) compare les deux tables via `payment_ref`.
    *   **Alertes :**
        *   *Manquant Provider :* Billet émis mais argent non reçu.
        *   *Manquant Système :* Argent reçu mais billet non émis (Orphelin).
        *   *Écart Montant :* Montant payé différent du prix du billet.

### Anti-Coulage (Gap Analysis)
*   **Comparaison Manifeste vs Réel :**
    *   L'administrateur upload le manifeste final de la compagnie (`FlightManifest`).
    *   Le système compte les passagers uniques scannés pour ce vol (`AccessLog` / `GoPass.status='consumed'`).
    *   **Alerte :** Si `Scannés > Manifeste`, il y a une anomalie potentielle (passagers non déclarés ou fraude agent).

## 3. Gestion Hybride des Vols

### Dualité des Sources
Le système gère deux types de vols pour couvrir l'ensemble du trafic aérien (National & International).

1.  **Vols API (Internationaux & Grands Nationaux) :**
    *   **Source :** AviationStack API.
    *   **Mise à jour :** Automatique (Statut, Horaires).
    *   **Avantage :** Fiabilité des données, gain de temps.

2.  **Vols Manuels (Brousse & Charters) :**
    *   **Source :** Saisie manuelle par l'Admin.
    *   **Usage :** Petits aérodromes non couverts par les GDS.
    *   **Flexibilité :** Permet de vendre des billets même si le vol n'est pas officiellement dans les systèmes internationaux.

### Tarification Dynamique
*   Les prix sont définis dans la table `Tariff` par combinaison :
    *   `Type de Vol` (National / International).
    *   `Catégorie Passager` (Adulte, Enfant, Bébé).
*   Lors de la vente, le système détecte le type de vol (via l'aéroport de destination ou la configuration du vol) et applique le tarif correspondant automatiquement.
