# SGI-GP - Guide de Déploiement

Ce document décrit la procédure d'installation et de mise en production de la plateforme **SGI-GP** sur un serveur Linux (Ubuntu 20.04 ou supérieur recommandé).

## 1. Pré-requis Système

*   **Système d'Exploitation :** Linux (Ubuntu/Debian) - Recommandé pour la production.
*   **Python :** Version 3.10 ou supérieure.
*   **Base de Données :** PostgreSQL 13+ (Production).
*   **Serveur Web :** Nginx (Proxy Reverse).
*   **Gestionnaire de Processus :** Systemd (Linux standard).

---

## 2. Installation de l'Application

### 2.1 Cloner le Dépôt
```bash
# Dans le dossier /var/www/ ou /home/ubuntu/
git clone https://github.com/votre-org/sgi-gp.git
cd sgi-gp
```

### 2.2 Environnement Virtuel Python
Il est impératif d'utiliser un environnement virtuel (`venv`) pour isoler les dépendances.
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Installation des Dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Configuration de l'Environnement

Créez un fichier `.env` à la racine du projet. Ce fichier contient les secrets de l'application et ne doit jamais être commité.

```bash
cp .env.example .env
nano .env
```

### Variables Critiques
| Variable | Description | Exemple (Ne pas copier tel quel) |
| :--- | :--- | :--- |
| `FLASK_ENV` | Environnement (`development` ou `production`) | `production` |
| `SESSION_SECRET` | Clé secrète pour signer les sessions | `super-secret-key-change-me` |
| `DATABASE_URL` | Chaîne de connexion PostgreSQL | `postgresql://user:pass@localhost:5432/sgi_db` |
| `AVIATIONSTACK_API_KEY` | Clé API pour la synchro des vols | `votre_cle_api` |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe (si paiement activé) | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Secret pour valider les webhooks Stripe | `whsec_...` |

**Note :** En production, si `FLASK_ENV=production` est défini, l'application refusera de démarrer si `DATABASE_URL` commence par `sqlite://`.

---

## 4. Initialisation de la Base de Données

Le script `init_db.py` crée les tables, les index et injecte les données de référence (Rôles, Tarifs par défaut, Admin).

```bash
# Assurez-vous d'être dans le venv et que le .env est configuré
python init_db.py
```
*Si tout se passe bien, vous verrez : "Database initialization completed successfully!"*

---

## 5. Mise en Production (Gunicorn & Nginx)

Ne jamais utiliser le serveur de développement Flask (`python app.py`) en production. Utilisez **Gunicorn**.

### 5.1 Test Rapide Gunicorn
```bash
# Lancer sur le port 8000 avec 4 workers
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
*Accédez à `http://IP_SERVEUR:8000` pour vérifier que l'application répond.*

### 5.2 Création du Service Systemd
Pour que l'application se lance au démarrage et redémarre en cas de crash.

Créez `/etc/systemd/system/sgi-gp.service` :
```ini
[Unit]
Description=Gunicorn instance to serve SGI-GP
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sgi-gp
Environment="PATH=/var/www/sgi-gp/venv/bin"
ExecStart=/var/www/sgi-gp/venv/bin/gunicorn --workers 4 --bind unix:sgi-gp.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

Activez le service :
```bash
sudo systemctl start sgi-gp
sudo systemctl enable sgi-gp
```

### 5.3 Configuration Nginx (Proxy Reverse)
Nginx gérera les fichiers statiques et la terminaison SSL (HTTPS).

Créez `/etc/nginx/sites-available/sgi-gp` :
```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/sgi-gp/sgi-gp.sock;
    }

    # Servir les fichiers statiques directement (Performance)
    location /static {
        alias /var/www/sgi-gp/statics;
        expires 30d;
    }
}
```

Activez le site et redémarrez Nginx :
```bash
sudo ln -s /etc/nginx/sites-available/sgi-gp /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. Maintenance & Troubleshooting

### Logs
*   **Gunicorn (Erreurs App) :** `journalctl -u sgi-gp -f`
*   **Nginx (Erreurs Web) :** `/var/log/nginx/error.log`

### Mises à Jour
Pour mettre à jour l'application :
1.  `git pull`
2.  `pip install -r requirements.txt` (si nouvelles dépendances)
3.  `python init_db.py` (si migrations de schéma nécessaires - le script gère l'ajout de colonnes manquantes)
4.  `sudo systemctl restart sgi-gp`

### Erreur Fréquente : "Internal Server Error" (500)
Vérifiez les logs Gunicorn. Souvent dû à une variable d'environnement manquante dans le `.env` ou une erreur de connexion à la base de données.
