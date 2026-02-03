# MANUEL OPÉRATIONNEL

Ce manuel décrit les procédures d'utilisation de la plateforme SGI-GP pour chaque rôle utilisateur.

## 1. Rôle : Super Admin

### Configuration Initiale & Paramètres
1.  **Gestion des Utilisateurs :**
    *   Accéder au menu `Utilisateurs`.
    *   Créer des comptes pour les agents (Percepteur, Contrôleur) et assigner leur aéroport (`location`).
    *   Définir les rôles et mots de passe initiaux.
2.  **Configuration Métier :**
    *   Aller dans `Paramètres` > `Tarifs` pour définir les prix (National/International, Adulte/Enfant).
    *   Configurer les `Aéroports` et `Compagnies Aériennes` autorisés.
    *   Activer/Désactiver les passerelles de paiement (`Stripe`, `Mobile Money`).

### Gestion des Vols
1.  **Synchronisation API :**
    *   Aller dans le module `Vols`.
    *   Cliquer sur `Synchroniser (AviationStack)` pour importer les vols du jour.
2.  **Création Manuelle (Vols Brousse) :**
    *   Si un vol n'apparaît pas, utiliser `Nouveau Vol` et saisir le numéro, l'heure et la capacité.
3.  **Audit des Manifestes :**
    *   Pour chaque vol clôturé, uploader le fichier Excel/PDF du manifeste compagnie via le bouton `Upload Manifeste`.
    *   Le système comparera automatiquement le nombre de passagers déclarés vs scannés.

### Rapports & Business Intelligence
*   **Tableau de Bord :** Suivre les ventes en temps réel et le "Gap Analysis" (Écart Manifeste vs Réel).
*   **Anti-Coulage :** Consulter les rapports d'anomalies (Billets scannés hors vol, tentatives de fraude).

## 2. Rôle : Agent Percepteur (POS)

### Procédure de Vente (Guichet)
1.  **Connexion :** Se connecter avec ses identifiants Agent.
2.  **Sélection du Vol :**
    *   Sur l'écran `POS`, choisir le vol correspondant au passager dans la liste des vols du jour.
3.  **Saisie Passager :**
    *   Entrer le `Nom`, `Prénom` et `Numéro de Passeport/ID`.
    *   Le système calcule automatiquement le prix selon le type de vol.
4.  **Paiement & Impression :**
    *   Confirmer la réception du paiement (Cash).
    *   Le système génère un ticket thermique.
    *   Imprimer le ticket et le remettre au passager.

### Clôture de Caisse
1.  **Fin de Service :**
    *   Aller dans le menu `Finances` > `Mes Ventes`.
    *   Vérifier le total théorique encaissé.
2.  **Dépôt :**
    *   Remettre les fonds au Superviseur.
    *   Le Superviseur valide le dépôt dans le système (Module Finance > Dépôts).

## 3. Rôle : Agent Contrôleur (Piste/Embarquement)

### Utilisation du Scanner
1.  **Initialisation :**
    *   Se connecter sur le terminal mobile (PDA ou Smartphone).
    *   Ouvrir le module `Scanner`.
    *   Autoriser l'accès à la caméra.
2.  **Scan des Passagers :**
    *   Viser le QR Code du passager.
    *   Attendre le signal visuel et sonore.

### Interprétation des Codes Couleurs
*   **🟢 VERT (VALIDE) :** Le passager peut embarquer. Le billet est marqué "Consommé".
*   **🔴 ROUGE (DÉJÀ SCANNÉ) :** **STOP !** Ce billet a déjà été utilisé. Vérifier l'historique affiché (heure du 1er scan).
*   **🔴 ROUGE (VOL CLÔTURÉ) :** Le vol est fermé ou le billet n'existe pas.
*   **🟠 ORANGE (MAUVAIS VOL) :** **ATTENTION !** Le billet est valide mais pour un **autre vol**. Vérifier la date et le numéro de vol sur le billet.

### Mode Hors-Ligne (Offline)
*   Si le réseau est coupé, le scanner continue de fonctionner en mode dégradé (vérification de signature si activée, ou mise en cache).
*   Dès le retour de la connexion, les scans sont synchronisés automatiquement avec le serveur central.

## 4. Rôle : Grand Public (E-GoPass)

### Parcours d'Achat Web
1.  **Recherche :**
    *   Accéder au portail public.
    *   Entrer la date et le numéro de vol (ou destination).
2.  **Achat :**
    *   Sélectionner le vol.
    *   Remplir les informations (Nom, Passeport).
    *   Payer en ligne (Carte Bancaire ou Mobile Money).
3.  **Récupération du Billet :**
    *   Une fois le paiement validé, télécharger le PDF (Format A4).
    *   Le billet peut être imprimé ou présenté sur mobile au contrôle.
