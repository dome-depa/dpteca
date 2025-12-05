#!/bin/bash
# Script di deploy per server Debian con Apache
# Uso: ./deploy.sh

set -e  # Esci in caso di errore

echo "🚀 Inizio deploy..."

# Attiva ambiente virtuale
source venv/bin/activate

# Aggiorna codice da GitHub
echo "📥 Aggiornamento codice da GitHub..."
git pull origin main

# Installa/aggiorna dipendenze
echo "📦 Installazione dipendenze..."
pip install -r requirements.txt --quiet

# Raccogli file statici
echo "📁 Raccolta file statici..."
python manage.py collectstatic --noinput

# Esegui migrazioni
echo "🗄️  Esecuzione migrazioni..."
python manage.py migrate --noinput

# Riavvia Apache
echo "🔄 Riavvio Apache..."
sudo systemctl reload apache2

echo "✅ Deploy completato con successo!"

