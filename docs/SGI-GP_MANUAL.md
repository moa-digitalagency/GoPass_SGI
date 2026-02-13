# SGI-GP - Manuel Utilisateur

Ce manuel décrit les procédures opérationnelles pour chaque profil utilisateur de la plateforme SGI-GP.

## 1. Rôle : Super Administrateur

### 1.1 Configuration Initiale
*   **Utilisateurs :** Créez les comptes pour vos équipes via le menu `Administration > Utilisateurs`. Assurez-vous d'attribuer le bon rôle (`Agent` ou `Contrôleur`) et l'aéroport de rattachement (`Location`).
*   **Tarifs :** Définissez les prix des GoPass dans `Paramètres > Tarifs`. Les prix peuvent varier selon le type de vol (National/International) et la catégorie de passager (Adulte/Enfant/Bébé).
*   **Logos :** Personnalisez les billets en chargeant les logos RVA et GoPass dans `Paramètres > Apparence`.

### 1.2 Gestion des Vols
*   **Synchronisation API :** Chaque matin, allez dans `Vols` et cliquez sur `Synchroniser` pour importer les vols du jour depuis AviationStack.
*   **Vols Manuels :** Si un vol (charter ou brousse) n'apparaît pas, utilisez le bouton `Nouveau Vol` pour le créer manuellement. Le numéro de vol doit être unique pour la journée.
*   **Audit Manifeste :** Après le décollage, récupérez le manifeste final de la compagnie et chargez-le via le bouton `Upload` sur la ligne du vol. Le système calculera automatiquement les écarts (Fraude potentielle).

### 1.3 Rapports & Finances
*   **Tableau de Bord :** Suivez en temps réel le nombre de billets vendus vs scannés.
*   **Clôture de Caisse :** Validez les dépôts d'espèces déclarés par les agents dans le menu `Finance > Dépôts`.

---

## 2. Rôle : Agent Percepteur (Guichet)

### 2.1 Vente de Billet (POS)
1.  Connectez-vous à votre terminal de vente.
2.  Sélectionnez le vol du passager dans la liste des départs du jour.
3.  Saisissez les informations du passager : `Nom`, `Prénom`, `Numéro Passeport/ID`.
4.  Le prix s'affiche automatiquement. Encaissez le montant (Cash).
5.  Cliquez sur **Valider**. L'imprimante thermique sortira le ticket avec son QR Code.

### 2.2 Fin de Service (Cash Drop)
1.  À la fin de votre shift, comptez votre caisse physique.
2.  Allez dans `Mon Profil > Mes Ventes` pour voir le total théorique attendu par le système.
3.  Si tout correspond, remettez l'argent au Superviseur.
4.  Une fois validé par le Superviseur, votre session de caisse est clôturée.

---

## 3. Rôle : Agent Contrôleur (Scanner)

### 3.1 Procédure de Contrôle
1.  Ouvrez l'application Scanner sur le PDA ou Smartphone de service.
2.  Positionnez-vous au filtre de sécurité ou à la porte d'embarquement.
3.  Visez le QR Code du passager. Le résultat s'affiche instantanément.

### 3.2 Codes Couleurs & Actions
*   **🟢 VERT (VALIDE) :** "Bon Voyage". Le passager peut passer. Le billet est instantanément marqué comme "Consommé" dans la base de données.
*   **🔴 ROUGE (DÉJÀ SCANNÉ) :** **STOP !** Ce billet a déjà été utilisé. L'écran affiche l'heure et l'agent du premier scan. C'est une tentative de fraude.
*   **🟠 ORANGE (MAUVAIS VOL) :** **ATTENTION !** Le billet est valide, mais pour un autre vol ou une autre date. Redirigez le passager vers le bon vol ou le guichet pour modification.
*   **🔴 ROUGE (INVALIDE/EXPIRÉ) :** Le billet est faux, expiré ou le vol est clôturé. Refusez l'accès.

### 3.3 Mode Hors-Ligne
Si le réseau coupe, continuez à scanner. Le terminal stockera les scans en mémoire tampon. Dès que la connexion revient, les données seront synchronisées automatiquement avec le serveur central.

---

## 4. Rôle : Grand Public (Web)

### 4.1 Achat en Ligne
1.  Rendez-vous sur le portail public GoPass.
2.  Recherchez votre vol par numéro ou destination.
3.  Remplissez vos informations personnelles.
4.  Payez par Carte Bancaire (Stripe) ou Mobile Money.
5.  Une fois le paiement confirmé, téléchargez votre E-GoPass (PDF A4) ou recevez-le par email.
6.  Présentez le QR Code sur votre smartphone lors du contrôle à l'aéroport.
