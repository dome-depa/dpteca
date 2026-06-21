#!/bin/bash
# Script di deploy per server Debian con Apache
# Uso: ./deploy.sh

set -e  # Esci in caso di errore

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
VENV="$ROOT/venv"
PYTHON="$VENV/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "Errore: ambiente virtuale non trovato in $VENV" >&2
    exit 1
fi

echo "🚀 Inizio deploy..."

# Aggiorna codice da GitHub
echo "📥 Aggiornamento codice da GitHub..."
git pull origin main

# Installa/aggiorna dipendenze
echo "📦 Installazione dipendenze..."
"$PYTHON" -m pip install -r requirements.txt --quiet

# Raccogli file statici
echo "📁 Raccolta file statici..."
"$PYTHON" manage.py collectstatic --noinput

# Esegui migrazioni
echo "🗄️  Esecuzione migrazioni..."
"$PYTHON" manage.py migrate --noinput

# Riavvia Apache
echo "🔄 Riavvio Apache..."
sudo systemctl reload apache2

echo "✅ Deploy completato con successo!"








