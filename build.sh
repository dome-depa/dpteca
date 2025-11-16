#!/usr/bin/env bash
# Build script per Render

set -o errexit  # Exit on error

echo "Building dPteca..."

# Installa dipendenze
pip install -r requirements.txt

# Raccoglie file statici
python manage.py collectstatic --noinput

# Esegue migrazioni
python manage.py migrate --noinput

echo "Build completato!"

