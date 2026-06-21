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

git_cmd() {
    env -u GIT_ASKPASS -u SSH_ASKPASS -u VSCODE_GIT_ASKPASS_NODE \
        -u VSCODE_GIT_ASKPASS_MAIN -u VSCODE_GIT_ASKPASS_EXTRA_ARGS \
        git "$@"
}

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

push_with_auth() {
    git_cmd push -u "$REMOTE" "$BRANCH"
}

sync_with_remote() {
    echo "📥 Sincronizzazione con $REMOTE/$BRANCH..."
    git_cmd fetch "$REMOTE" "$BRANCH"

    local behind
    behind="$(git rev-list --count HEAD.."$REMOTE/$BRANCH" 2>/dev/null || echo 0)"
    if [[ "${behind:-0}" -gt 0 ]]; then
        echo "⬇️  Integrazione di $behind commit da GitHub (rebase)..."
        git_cmd pull --rebase "$REMOTE" "$BRANCH"
    fi
}

report_push_failure() {
    local output="$1"
    echo "" >&2
    if grep -qiE 'fetch first|non-fast-forward|rejected' <<< "$output"; then
        echo "❌ Push rifiutato: su GitHub ci sono commit che non hai in locale." >&2
        echo "Esegui:" >&2
        echo "  git pull --rebase origin main" >&2
        echo "  ./push_github.sh --push-only" >&2
        return
    fi
    if grep -qiE '401|403|authentication|permission denied|invalid credentials' <<< "$output"; then
        echo "❌ Push fallito: autenticazione GitHub non valida." >&2
        echo "" >&2
        echo "Opzioni consigliate:" >&2
        echo "  1) SSH: aggiungi la chiave pubblica su GitHub → Settings → SSH keys" >&2
        echo "     cat ~/.ssh/id_ed25519.pub" >&2
        echo "  2) HTTPS: usa un Personal Access Token al posto della password GitHub" >&2
        echo "  3) GitHub CLI: gh auth login" >&2
        return
    fi
    echo "❌ Push fallito." >&2
    echo "$output" >&2
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

sync_with_remote

LOCAL_COMMITS="$(git rev-list --count "$REMOTE/$BRANCH"..HEAD 2>/dev/null || true)"
if [[ "${LOCAL_COMMITS:-0}" -eq 0 ]]; then
    echo "ℹ️  Nessun commit locale da inviare su GitHub."
    exit 0
fi

echo "🚀 Push su $REMOTE/$BRANCH ($LOCAL_COMMITS commit)..."
PUSH_OUTPUT=""
if ! PUSH_OUTPUT="$(push_with_auth 2>&1)"; then
    report_push_failure "$PUSH_OUTPUT"
    exit 1
fi
if [[ -n "$PUSH_OUTPUT" ]]; then
    echo "$PUSH_OUTPUT"
fi

echo "✅ Aggiornamento su GitHub completato."
