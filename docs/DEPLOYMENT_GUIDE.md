# GUIDE DE DÉPLOIEMENT

Ce document décrit la procédure d'installation et de mise en production de l'application SGI-GP.

## 1. Pré-requis Système

*   **OS :** Linux (Ubuntu 20.04+ recommandé)
*   **Langage :** Python 3.8 ou supérieur
*   **Base de Données :** PostgreSQL 12+ (Production) ou SQLite (Développement)
*   **Serveur Web :** Nginx (Recommandé en front de Gunicorn)

## 2. Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/votre-org/sgi-gp.git
cd sgi-gp
```

### 2. Environnement Virtuel
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Dépendances Backend (Python)
```bash
pip install -r requirements.txt
```

### 4. Dépendances Frontend (Node.js)
Si vous devez recompiler les assets CSS (Tailwind) ou JS :
```bash
npm install
npm run build
```

## 3. Configuration

Créer un fichier `.env` à la racine du projet en copiant `.env.example` (s'il existe) ou avec les valeurs suivantes :

```bash
# General
FLASK_ENV=production
SECRET_KEY=generer-une-cle-secrete-forte-ici

# Database (PostgreSQL)
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/sgi_gp_db
# Ou SQLite (par défaut si non défini)
# SQLALCHEMY_DATABASE_URI=sqlite:///gopass.db

# AviationStack API (Pour la synchro des vols)
AVIATIONSTACK_API_KEY=votre_cle_api_aviationstack

# Security
# Clé privée pour signature si nécessaire (actuellement hash SHA256)
PRIVATE_KEY_PATH=/path/to/private.pem
```

## 4. Initialisation de la Base de Données

Le script `init_db.py` crée les tables et injecte les données de référence (Tarifs, Aéroports, Rôles Admin par défaut).

```bash
python init_db.py
```

*Vérifier la sortie pour confirmer que "Database initialization completed successfully!".*

## 5. Mise en Production

### 1. Test avec Gunicorn
Lancer le serveur WSGI manuellement pour tester :
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
Accéder à `http://<IP_SERVEUR>:8000`.

### 2. Service Systemd (Persistance)
Créer le fichier `/etc/systemd/system/sgi-gp.service` :

```ini
[Unit]
Description=Gunicorn instance to serve SGI-GP
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/sgi-gp
Environment="PATH=/home/ubuntu/sgi-gp/venv/bin"
ExecStart=/home/ubuntu/sgi-gp/venv/bin/gunicorn --workers 4 --bind unix:sgi-gp.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

Activer le service :
```bash
sudo systemctl start sgi-gp
sudo systemctl enable sgi-gp
```

### 3. Configuration Nginx (Proxy Reverse)
Créer `/etc/nginx/sites-available/sgi-gp` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/sgi-gp/sgi-gp.sock;
    }

    location /static {
        alias /home/ubuntu/sgi-gp/statics;
    }
}
```

Activer le site :
```bash
sudo ln -s /etc/nginx/sites-available/sgi-gp /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 6. Maintenance

*   **Logs Gunicorn :** `journalctl -u sgi-gp`
*   **Logs Application :** Voir configuration logging Flask (par défaut stdout/stderr).
*   **Backup DB :** Utiliser `pg_dump` pour PostgreSQL quotidiennement.
