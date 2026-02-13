# SGI-GP - Stratégie Métier & Règles de Gestion

Ce document détaille les choix d'implémentation stratégiques du SGI-GP, conçus pour maximiser les recettes aéroportuaires et garantir une traçabilité totale ("Zero Trust").

## 1. Principe "Flight-Bound" (Liaison Vol Unique)

### 1.1 Le Concept
Contrairement aux systèmes de "portefeuille" ou de "crédit temps", le SGI-GP applique une règle stricte :
**1 Billet = 1 Vol Spécifique = 1 Date Unique.**

### 1.2 Justification Technique & Commerciale
*   **Sécurité :** Empêche la réutilisation d'un billet valide sur un autre vol (fraude par substitution).
*   **Audit :** Permet la réconciliation exacte entre le manifeste de la compagnie aérienne et les scans réalisés au sol.
*   **Expérience Passager :** Garantit une place à bord (pas de surbooking lié au GoPass).

### 1.3 Implémentation
*   La table `GoPass` contient une clé étrangère `flight_id` non nulle.
*   Le scanner vérifie dynamiquement la correspondance entre le billet et le vol en cours d'embarquement (Code Orange si divergence).

---

## 2. Maximisation des Recettes & Anti-Fraude

### 2.1 Sécurisation du Cash (Guichet)
Le risque majeur en aéroport est le non-reversement des espèces encaissées par les agents.
*   **Traçabilité Agent :** Chaque vente est signée par l'ID de l'agent connecté (`sold_by`).
*   **Total Théorique :** Le système calcule en temps réel le montant dû par chaque guichetier.
*   **Verrouillage :** L'agent doit déclarer son fond de caisse (`CashDeposit`) avant de pouvoir clôturer sa session. Tout écart est signalé au superviseur.

### 2.2 Réconciliation Mobile Money
Pour contrer les faux SMS de paiement :
*   **Double Entrée Comptable :**
    1.  Statut du ticket dans `GoPass` (métier).
    2.  Log brut du provider dans `MobileMoneyLog` (financier).
*   **Algorithme de Matching :** Un processus compare les deux tables via `payment_ref`.
    *   *Alerte :* Billet émis sans argent reçu.
    *   *Alerte :* Argent reçu sans billet émis (Orphelin).

### 2.3 Anti-Coulage (Gap Analysis)
L'outil ultime de contrôle est la comparaison **Manifeste vs Réel**.
*   **Procédure :** L'administrateur upload le manifeste final (PDF/Excel) fourni par la compagnie après le décollage.
*   **Analyse :** Le système croise le nombre de passagers déclarés avec le nombre de scans uniques (`AccessLog`).
*   **Résultat :** Si `Scannés > Manifeste`, une alerte de fraude est déclenchée (Passagers clandestins ou non déclarés).

---

## 3. Gestion Hybride des Vols

Pour couvrir 100% du trafic (Lignes régulières + Aviation d'affaires/Brousse), le système adopte une approche hybride :

1.  **Vols API (Automatisés) :**
    *   Via *AviationStack*.
    *   Couverture : Vols internationaux et grands nationaux.
    *   Avantage : Fiabilité horaire, mises à jour de statut en temps réel.

2.  **Vols Manuels (Dégradés) :**
    *   Saisie par l'opérateur.
    *   Couverture : Petits porteurs, vols privés, zones non couvertes par les GDS.
    *   Validation : Unicité du numéro de vol/date pour éviter les doublons.

---

## 4. Tarification Dynamique

Le modèle de prix est flexible pour s'adapter aux politiques commerciales :
*   **Critères :** Type de vol (National / International), Catégorie Passager (Adulte / Enfant / Bébé).
*   **Devise :** Gestion multi-devises (USD par défaut, conversion taux du jour pour les paiements locaux).
*   **Mise à jour :** Modifiable à chaud par le Super Admin sans redéploiement.
