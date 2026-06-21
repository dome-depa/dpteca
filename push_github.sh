#!/bin/bash
# Pubblica le modifiche locali su GitHub.
#
# Uso:
#   ./push_github.sh "Messaggio di commit"
#   ./push_github.sh                      # chiede il messaggio
#   ./push_github.sh --push-only          # solo push, senza nuovo commit
#   ./push_github.sh --status             # mostra solo lo stato del repository
#
# Variabili opzionali:
#   BRANCH=main REMOTE=origin ./push_github.sh "messaggio"

set -euo pipefail

REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
PUSH_ONLY=0
SHOW_STATUS=0
COMMIT_MESSAGE=""

usage() {
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --push-only)
            PUSH_ONLY=1
            shift
            ;;
        --status)
            SHOW_STATUS=1
            shift
            ;;
        *)
            COMMIT_MESSAGE="$1"
            shift
            ;;
    esac
done

cd "$(dirname "$0")"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Errore: questa cartella non è un repository git." >&2
    exit 1
fi

echo "📋 Repository: $(git remote get-url "$REMOTE" 2>/dev/null || echo "$REMOTE")"
echo "🌿 Branch: $BRANCH"
echo ""
git status -sb
echo ""

if [[ "$SHOW_STATUS" -eq 1 ]]; then
    exit 0
fi

block_sensitive_files() {
  local sensitive_patterns=(
    '.env'
    '.env.*'
    'credentials.json'
    '*.pem'
    '*.key'
    'id_rsa'
    'id_ed25519'
  )
  local staged
  staged="$(git diff --cached --name-only 2>/dev/null || true)"
  if [[ -z "$staged" ]]; then
    return 0
  fi
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    local base
    base="$(basename "$file")"
  for pattern in "${sensitive_patterns[@]}"; do
      if [[ "$base" == $pattern ]] || [[ "$file" == $pattern ]]; then
        echo "Errore: file sensibile in staging: $file" >&2
        echo "Rimuovilo dal commit prima di continuare." >&2
        exit 1
      fi
    done
  done <<< "$staged"
}

if [[ "$PUSH_ONLY" -eq 0 ]]; then
    if [[ -z "$COMMIT_MESSAGE" ]]; then
        read -r -p "Messaggio di commit: " COMMIT_MESSAGE
    fi

    if [[ -z "$COMMIT_MESSAGE" ]]; then
        echo "Errore: messaggio di commit obbligatorio." >&2
        exit 1
    fi

    if git diff --quiet && git diff --cached --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
        echo "ℹ️  Nessuna modifica da committare."
    else
        echo "➕ Aggiunta file al commit..."
        git add -A
        block_sensitive_files

        echo "💾 Creazione commit..."
        git commit -m "$COMMIT_MESSAGE"
    fi
fi

LOCAL_COMMITS="$(git rev-list --count "$REMOTE/$BRANCH"..HEAD 2>/dev/null || true)"
if [[ "${LOCAL_COMMITS:-0}" -eq 0 ]]; then
    echo "ℹ️  Nessun commit locale da inviare su GitHub."
    exit 0
fi

echo "🚀 Push su $REMOTE/$BRANCH ($LOCAL_COMMITS commit)..."
git push -u "$REMOTE" "$BRANCH"

echo "✅ Aggiornamento su GitHub completato."
