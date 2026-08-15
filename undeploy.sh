#!/bin/bash
# Mette offline (o di nuovo online) il sito dpteca su Apache.
#
# Uso:
#   ./undeploy.sh              # disabilita i VirtualHost e ricarica Apache
#   ./undeploy.sh --online     # riabilita i VirtualHost (annulla undeploy)
#   ./undeploy.sh --status     # mostra se i siti sono attivi
#   ./undeploy.sh -h|--help
#
# Non elimina codice, venv, database, media o certificati SSL.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

SITES=(
    "dpteca.casanausicaa.it.conf"
    "dpteca.casanausicaa.it-ssl.conf"
)

MODE="offline"
SHOW_STATUS=0

usage() {
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --online|--enable)
            MODE="online"
            shift
            ;;
        --offline|--disable)
            MODE="offline"
            shift
            ;;
        --status)
            SHOW_STATUS=1
            shift
            ;;
        *)
            echo "Opzione sconosciuta: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

site_enabled() {
    local site="$1"
    [[ -e "/etc/apache2/sites-enabled/$site" ]]
}

print_status() {
    echo "📋 Stato siti Apache dpteca:"
    local site
    for site in "${SITES[@]}"; do
        if site_enabled "$site"; then
            echo "  ✅ abilitato: $site"
        else
            echo "  ⏸️  disabilitato: $site"
        fi
    done
}

reload_apache() {
    echo "🔄 Ricarica Apache..."
    if sudo systemctl reload apache2; then
        echo "✅ Apache ricaricato."
    else
        echo "⚠️  reload fallito, provo restart..." >&2
        sudo systemctl restart apache2
        echo "✅ Apache riavviato."
    fi
}

if [[ "$SHOW_STATUS" -eq 1 ]]; then
    print_status
    exit 0
fi

echo "📋 Repository: $ROOT"
print_status
echo ""

if [[ "$MODE" == "offline" ]]; then
    echo "🛑 Undeploy: disabilitazione siti dpteca..."
    local_disabled=0
    for site in "${SITES[@]}"; do
        if site_enabled "$site"; then
            echo "  − a2dissite $site"
            sudo a2dissite "$site" >/dev/null
            local_disabled=1
        else
            echo "  · già disabilitato: $site"
        fi
    done
    if [[ "$local_disabled" -eq 1 ]]; then
        reload_apache
    else
        echo "ℹ️  Nessun sito da disabilitare."
    fi
    echo ""
    echo "✅ Sito offline. Codice, DB e media sono intatti."
    echo "   Per rimetterlo online: ./undeploy.sh --online && ./deploy.sh"
else
    echo "🟢 Online: abilitazione siti dpteca..."
    local_enabled=0
    for site in "${SITES[@]}"; do
        available="/etc/apache2/sites-available/$site"
        if [[ ! -f "$available" ]]; then
            echo "Errore: manca $available" >&2
            exit 1
        fi
        if site_enabled "$site"; then
            echo "  · già abilitato: $site"
        else
            echo "  + a2ensite $site"
            sudo a2ensite "$site" >/dev/null
            local_enabled=1
        fi
    done
    if [[ "$local_enabled" -eq 1 ]]; then
        reload_apache
    else
        echo "ℹ️  Siti già abilitati."
        reload_apache
    fi
    echo ""
    echo "✅ Siti riabilitati. Consigliato: ./deploy.sh"
fi

echo ""
print_status
