#!/bin/bash
# Deploy del progetto dpteca sul server locale (Debian + Apache + PostgreSQL).
#
# Uso:
#   ./deploy.sh              # pull da GitHub + dipendenze + migrate + static + reload Apache
#   ./deploy.sh --local      # senza git pull (solo applicativo locale)
#   ./deploy.sh --check      # solo controlli (venv, .env, django check)
#   ./deploy.sh -h|--help
#
# Variabili opzionali:
#   BRANCH=main REMOTE=origin ./deploy.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
VENV="$ROOT/venv"
PYTHON="$VENV/bin/python"
SKIP_PULL=0
CHECK_ONLY=0

APACHE_SITES=(
    "dpteca.casanausicaa.it.conf"
    "dpteca.casanausicaa.it-ssl.conf"
)

usage() {
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
}

git_cmd() {
    env -u GIT_ASKPASS -u SSH_ASKPASS -u VSCODE_GIT_ASKPASS_NODE \
        -u VSCODE_GIT_ASKPASS_MAIN -u VSCODE_GIT_ASKPASS_EXTRA_ARGS \
        git "$@"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --local)
            SKIP_PULL=1
            shift
            ;;
        --check)
            CHECK_ONLY=1
            shift
            ;;
        *)
            echo "Opzione sconosciuta: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

echo "🚀 Deploy dpteca"
echo "📁 Root: $ROOT"
echo ""

if [[ ! -x "$PYTHON" ]]; then
    echo "Errore: venv non trovato in $VENV" >&2
    echo "Crea con: python3 -m venv venv && venv/bin/python -m pip install -r requirements.txt" >&2
    exit 1
fi

if [[ ! -f "$ROOT/.env" ]]; then
    echo "⚠️  Manca .env — copialo da .env.example e compila DB_PASSWORD / YOUTUBE_API_KEY"
    if [[ -f "$ROOT/.env.example" ]]; then
        echo "   cp .env.example .env"
    fi
    echo ""
fi

echo "🔎 Django check..."
"$PYTHON" manage.py check

if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "✅ Controlli ok."
    exit 0
fi

if [[ "$SKIP_PULL" -eq 0 ]]; then
    if git_cmd rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "📥 Aggiornamento codice da $REMOTE/$BRANCH..."
        if ! git_cmd diff --quiet || ! git_cmd diff --cached --quiet; then
            echo "⚠️  Ci sono modifiche locali non committate: il pull potrebbe fallire."
            git_cmd status -sb
        fi
        git_cmd pull --ff-only "$REMOTE" "$BRANCH"
    else
        echo "⚠️  Non è un repository git: salto il pull."
    fi
else
    echo "ℹ️  Modalità --local: salto git pull."
fi

echo "📦 Installazione dipendenze..."
"$PYTHON" -m pip install -r requirements.txt --quiet

echo "🗄️  Migrazioni..."
"$PYTHON" manage.py migrate --noinput

echo "📁 Collectstatic..."
"$PYTHON" manage.py collectstatic --noinput

echo "🔄 Ricarica applicazione..."
APACHE_OK=0
if command -v systemctl >/dev/null 2>&1; then
    if sudo -n systemctl reload apache2 2>/dev/null; then
        APACHE_OK=1
        echo "✅ Apache ricaricato (sudo senza password)."
    elif sudo systemctl reload apache2; then
        APACHE_OK=1
        echo "✅ Apache ricaricato."
    fi
fi

if [[ "$APACHE_OK" -eq 0 ]]; then
    touch "$ROOT/dpteca/wsgi.py"
    echo "⚠️  Reload Apache non riuscito: toccato wsgi.py per ricaricare i worker WSGI."
fi

echo ""
echo "📋 Siti Apache dpteca:"
for site in "${APACHE_SITES[@]}"; do
    if [[ -e "/etc/apache2/sites-enabled/$site" ]]; then
        echo "  ✅ $site"
    else
        echo "  ⏸️  non abilitato: $site  (sudo a2ensite $site && sudo systemctl reload apache2)"
    fi
done

echo ""
echo "✅ Deploy completato."
