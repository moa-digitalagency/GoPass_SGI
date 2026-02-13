# SGI-GP (Système de Gestion Intégrée - GoPass)

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-1.2.0-blue)
![License](https://img.shields.io/badge/license-Proprietary-red)
![Stack](https://img.shields.io/badge/tech-Flask%20%7C%20PostgreSQL%20%7C%20Tailwind-orange)

**La solution souveraine de sécurisation des recettes aéroportuaires.**

SGI-GP est une plateforme complète de gestion des titres de transport ("GoPass") conçue pour les environnements aéroportuaires à haute contrainte. Elle garantit la traçabilité financière de chaque passager, du paiement au guichet jusqu'à l'embarquement, en éliminant la fraude et le coulage des recettes.

---

## 📚 Documentation Complète

Toute la documentation technique et fonctionnelle se trouve dans le dossier `docs/` :

*   📖 **[Bible des Fonctionnalités](docs/SGI-GP_features_full_list.md)** : Le détail exhaustif de chaque module.
*   🏗 **[Architecture Technique](docs/SGI-GP_ARCHITECTURE.md)** : Stack, Modèle de Données, Sécurité.
*   🚀 **[Guide de Déploiement](docs/SGI-GP_DEPLOYMENT.md)** : Installation Serveur & Production.
*   📘 **[Manuel Utilisateur](docs/SGI-GP_MANUAL.md)** : Guides pour Agents, Contrôleurs et Admins.
*   🎯 **[Stratégie Métier](docs/SGI-GP_STRATEGY.md)** : Règles de gestion "Flight-Bound" et Anti-Fraude.
*   🔌 **[API Reference](docs/SGI-GP_API.md)** : Endpoints pour intégration Mobile/Web.

---

## 🌟 Fonctionnalités Clés

### 1. Sécurité "Flight-Bound"
Un billet n'est valide que pour **un vol spécifique** à une **date précise**. Le scanner rejette automatiquement toute tentative de réutilisation sur un autre vol (Code Orange/Rouge).

### 2. Anti-Fraude & Audit
*   **Réconciliation Manifeste :** Comparaison automatique entre les passagers déclarés par la compagnie et les scans réels.
*   **Cash Control :** Gestion stricte des caisses agents avec déclaration obligatoire (`CashDrop`) en fin de service.
*   **Logs Immuables :** Chaque scan (Valide ou Rejeté) est historisé avec géolocalisation et ID agent.

### 3. Gestion Hybride des Vols
*   **Automatique :** Synchronisation temps réel via API (AviationStack) pour les vols internationaux.
*   **Manuel :** Saisie dégradée pour les vols brousse/charters non répertoriés.

### 4. Expérience Omni-canal
*   **Grand Public :** Achat Web (Stripe/Mobile Money) et E-Billet A4.
*   **Guichet (POS) :** Vente rapide (3 clics) et impression thermique 80mm.

---

## 🛠 Stack Technique

*   **Backend :** Python 3.10, Flask 3.0, SQLAlchemy.
*   **Base de Données :** PostgreSQL 13+ (Prod), SQLite (Dev).
*   **Frontend :** Jinja2 (SSR), Tailwind CSS, JavaScript (Vanilla).
*   **Édition :** ReportLab (Moteur PDF haute performance), Pillow.
*   **Infra :** Gunicorn, Nginx, Docker (Optionnel).

---

## 🚀 Démarrage Rapide (Développement)

### Pré-requis
*   Python 3.8+
*   `pip` et `venv`

### Installation
```bash
# 1. Cloner le projet
git clone https://github.com/votre-org/sgi-gp.git
cd sgi-gp

# 2. Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env
# Modifiez .env avec vos clés API (AviationStack, Stripe)

# 5. Initialiser la Base de Données
python init_db.py

# 6. Lancer le serveur
flask run
```
Accédez à `http://localhost:5000`.

---

## 🔒 Sécurité

Ce projet a été audité par **La CyberConfiance**.
Il implémente les standards OWASP :
*   Protection CSRF sur tous les formulaires.
*   En-têtes de sécurité stricts (HSTS, CSP).
*   Hachage des mots de passe (Argon2/PBKDF2).
*   Sanitization des entrées utilisateurs.

---

**© 2024 MOA Digital Agency.** Tous droits réservés.
