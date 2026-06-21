#!/usr/bin/env bash
set -euo pipefail

OLD_IP="${1:-}"
NEW_IP="${2:-95.251.150.147}"

if [[ -z "${OLD_IP}" ]]; then
  echo "Usage: $0 <old_ip> [new_ip]" >&2
  exit 1
fi

ROOTS=(
  /etc/apache2
  /home/vipera/dpteca
  /var/www
)

echo "Searching for ${OLD_IP} ..."
rg --fixed-strings --no-messages "${OLD_IP}" "${ROOTS[@]}" || true

python - "$OLD_IP" "$NEW_IP" "${ROOTS[@]}" <<'PY'
import os
import sys

old_ip = sys.argv[1]
new_ip = sys.argv[2]
roots = sys.argv[3:]

def should_skip(path: str) -> bool:
    parts = path.split(os.sep)
    return any(p in (".git", "node_modules", "venv", "__pycache__") for p in parts)

replaced = []

for root in roots:
    if not os.path.exists(root):
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        if should_skip(dirpath):
            dirnames[:] = []
            continue
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                with open(path, "rb") as handle:
                    data = handle.read()
            except (PermissionError, IsADirectoryError):
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if old_ip not in text:
                continue
            new_text = text.replace(old_ip, new_ip)
            try:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(new_text)
            except PermissionError:
                continue
            replaced.append(path)

print("Replaced in:")
for path in replaced:
    print(path)
PY

echo "Done. Reload services if needed (e.g., Apache)."
