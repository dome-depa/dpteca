# Guida al Deployment su Debian con Apache

Questa guida ti accompagna passo-passo per migrare il progetto Django da Render a un server Linux Debian con Apache e PostgreSQL.

---

## 📋 Prerequisiti

- Server Debian 11/12 con accesso root o sudo
- Dominio configurato (opzionale ma consigliato per SSL)
- Accesso SSH al server

---

## 🔧 Fase 1: Preparazione del Server

### 1.1 Aggiorna il sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Installa dipendenze di sistema

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    apache2 \
    libapache2-mod-wsgi-py3 \
    git \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    certbot \
    python3-certbot-apache
```

---

## 🗄️ Fase 2: Configurazione PostgreSQL

### 2.1 Crea database e utente

```bash
sudo -u postgres psql
```

Nel prompt PostgreSQL:

```sql
-- Crea database
CREATE DATABASE dpteca_db;

-- Crea utente
CREATE USER dpteca_user WITH PASSWORD 'TUA_PASSWORD_SICURA_QUI';

-- Concedi privilegi
GRANT ALL PRIVILEGES ON DATABASE dpteca_db TO dpteca_user;

-- Per PostgreSQL 15+, abilita anche lo schema pubblico
\c dpteca_db
GRANT ALL ON SCHEMA public TO dpteca_user;

-- Esci
\q
```

### 2.2 Configura accesso PostgreSQL (opzionale)

Modifica `/etc/postgresql/*/main/pg_hba.conf` se necessario per permettere connessioni locali:

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Assicurati che ci sia questa riga:
```
local   all             all                                     md5
```

Riavvia PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## 📁 Fase 3: Setup Progetto Django

### 3.1 Crea utente per l'applicazione (opzionale ma consigliato)

```bash
sudo adduser --disabled-password --gecos "" dpteca
sudo su - dpteca
```

### 3.2 Clona il repository

```bash
cd /home/dpteca
git clone https://github.com/dome-depa/dpteca.git mysite
cd mysite
```

### 3.3 Crea ambiente virtuale

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.4 Installa dipendenze Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.5 Crea directory per file statici e media

```bash
mkdir -p /home/dpteca/mysite/staticfiles
mkdir -p /home/dpteca/media-serve
chmod -R 755 /home/dpteca/media-serve
```

---

## ⚙️ Fase 4: Configurazione Django

### 4.1 Crea file `.env` per variabili d'ambiente

```bash
cd /home/dpteca/mysite
nano .env
```

Aggiungi:

```bash
SECRET_KEY=GENERA_UNA_CHIAVE_SICURA_QUI
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com,IP_DEL_SERVER
DB_NAME=dpteca_db
DB_USER=dpteca_user
DB_PASSWORD=TUA_PASSWORD_SICURA_QUI
DB_HOST=localhost
DB_PORT=5432
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@tudominio.com
SUPERUSER_PASSWORD=password_sicura_admin
```

**Genera SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4.2 Modifica `settings.py` per caricare `.env`

Aggiungi all'inizio di `mysite/settings.py`:

```python
from pathlib import Path
import os
from dotenv import load_dotenv  # Aggiungi questa riga

# Carica variabili da .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
```

E modifica le sezioni relative:

```python
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

allowed_hosts_str = os.environ.get('ALLOWED_HOSTS', 'localhost')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',') if host.strip()]
```

E per il database:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'dpteca_db'),
        'USER': os.environ.get('DB_USER', 'dpteca_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

**Installa python-dotenv:**
```bash
pip install python-dotenv
echo "python-dotenv>=1.0.0" >> requirements.txt
```

### 4.3 Rimuovi WhiteNoise (Apache servirà i file statici)

In `settings.py`, commenta o rimuovi:
```python
# 'whitenoise.middleware.WhiteNoiseMiddleware',  # Non necessario con Apache
```

E modifica:
```python
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # Commenta
```

### 4.4 Raccogli file statici

```bash
python manage.py collectstatic --noinput
```

### 4.5 Esegui migrazioni e carica dati

```bash
python manage.py migrate
python manage.py loaddata data_export.json
```

### 4.6 Crea superuser (se non esiste già)

```bash
python manage.py createsuperuser
```

---

## 🌐 Fase 5: Configurazione Apache

### 5.1 Crea file di configurazione Apache

```bash
sudo nano /etc/apache2/sites-available/dpteca.conf
```

Aggiungi:

```apache
<VirtualHost *:80>
    ServerName tudominio.com
    ServerAlias www.tudominio.com
    
    # Directory del progetto
    DocumentRoot /home/dpteca/mysite
    
    # Directory per file statici
    Alias /static /home/dpteca/mysite/staticfiles
    <Directory /home/dpteca/mysite/staticfiles>
        Require all granted
    </Directory>
    
    # Directory per file media
    Alias /media /home/dpteca/media-serve
    <Directory /home/dpteca/media-serve>
        Require all granted
    </Directory>
    
    # Configurazione WSGI
    WSGIDaemonProcess dpteca python-home=/home/dpteca/mysite/venv python-path=/home/dpteca/mysite
    WSGIProcessGroup dpteca
    WSGIScriptAlias / /home/dpteca/mysite/mysite/wsgi.py
    
    <Directory /home/dpteca/mysite/mysite>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    
    # Permetti accesso a tutto il progetto
    <Directory /home/dpteca/mysite>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    
    # Log
    ErrorLog ${APACHE_LOG_DIR}/dpteca_error.log
    CustomLog ${APACHE_LOG_DIR}/dpteca_access.log combined
</VirtualHost>
```

### 5.2 Abilita il sito e mod_wsgi

```bash
sudo a2ensite dpteca.conf
sudo a2enmod wsgi
sudo a2enmod rewrite
sudo systemctl reload apache2
```

### 5.3 Disabilita il sito di default (opzionale)

```bash
sudo a2dissite 000-default.conf
sudo systemctl reload apache2
```

### 5.4 Verifica configurazione

```bash
sudo apache2ctl configtest
```

Se tutto è OK, riavvia Apache:
```bash
sudo systemctl restart apache2
```

---

## 🔒 Fase 6: Configurazione SSL (Let's Encrypt)

### 6.1 Ottieni certificato SSL

```bash
sudo certbot --apache -d tudominio.com -d www.tudominio.com
```

Segui le istruzioni. Certbot modificherà automaticamente la configurazione Apache.

### 6.2 Rinnovo automatico

Il rinnovo è già configurato automaticamente. Verifica:

```bash
sudo certbot renew --dry-run
```

---

## 🔄 Fase 7: Script di Deploy

Crea uno script per semplificare i futuri deploy:

```bash
nano /home/dpteca/deploy.sh
```

Aggiungi:

```bash
#!/bin/bash
cd /home/dpteca/mysite
source venv/bin/activate
git pull origin main
pip install -r requirements.txt --quiet
python manage.py collectstatic --noinput
python manage.py migrate --noinput
sudo systemctl reload apache2
echo "Deploy completato!"
```

Rendi eseguibile:

```bash
chmod +x /home/dpteca/deploy.sh
```

---

## 🛠️ Fase 8: Ottimizzazioni e Sicurezza

### 8.1 Permessi file

```bash
sudo chown -R dpteca:www-data /home/dpteca/mysite
sudo chown -R dpteca:www-data /home/dpteca/media-serve
sudo chmod -R 755 /home/dpteca/mysite
sudo chmod -R 755 /home/dpteca/media-serve
```

### 8.2 Firewall (UFW)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

### 8.3 Backup automatico database

Crea script di backup:

```bash
nano /home/dpteca/backup_db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/dpteca/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U dpteca_user -h localhost dpteca_db > $BACKUP_DIR/db_backup_$DATE.sql
# Mantieni solo gli ultimi 7 backup
ls -t $BACKUP_DIR/db_backup_*.sql | tail -n +8 | xargs rm -f
```

Aggiungi a crontab (backup giornaliero alle 2:00):

```bash
crontab -e
```

Aggiungi:
```
0 2 * * * /home/dpteca/backup_db.sh
```

---

## 🐛 Troubleshooting

### Apache non si avvia

```bash
sudo systemctl status apache2
sudo journalctl -xe
sudo apache2ctl configtest
```

### Errori di permessi

```bash
sudo chown -R dpteca:www-data /home/dpteca/mysite
sudo chmod -R 755 /home/dpteca/mysite
```

### Database non si connette

```bash
sudo -u postgres psql -c "\l"  # Lista database
sudo -u postgres psql dpteca_db  # Test connessione
```

### File statici non si vedono

```bash
python manage.py collectstatic --noinput
sudo systemctl restart apache2
```

### Log Apache

```bash
sudo tail -f /var/log/apache2/dpteca_error.log
sudo tail -f /var/log/apache2/dpteca_access.log
```

### Log Django

Aggiungi in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/dpteca/mysite/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## ✅ Checklist Finale

- [ ] Server aggiornato
- [ ] PostgreSQL installato e configurato
- [ ] Database e utente creati
- [ ] Progetto clonato da GitHub
- [ ] Ambiente virtuale creato e dipendenze installate
- [ ] File `.env` configurato
- [ ] `settings.py` modificato per produzione
- [ ] File statici raccolti (`collectstatic`)
- [ ] Migrazioni eseguite
- [ ] Dati caricati (`loaddata`)
- [ ] Apache configurato con mod_wsgi
- [ ] SSL configurato (Let's Encrypt)
- [ ] Firewall configurato
- [ ] Backup automatico configurato
- [ ] Sito accessibile e funzionante

---

## 📚 Risorse Utili

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Apache mod_wsgi Documentation](https://modwsgi.readthedocs.io/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

**Buon deploy! 🚀**

