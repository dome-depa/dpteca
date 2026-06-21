#!/bin/bash
# Configura tastiera italiana (tastiera fisica EU / 105 tasti).
# Uso: ./scripts/set_italian_keyboard.sh
# Per rendere permanente a livello di sistema: sudo ./scripts/set_italian_keyboard.sh --system

set -euo pipefail

USER_SCRIPT="$HOME/.local/bin/set-italian-keyboard.sh"
INSTALL_USER=1
INSTALL_SYSTEM=0

if [[ "${1:-}" == "--system" ]]; then
    INSTALL_SYSTEM=1
fi

mkdir -p "$HOME/.local/bin" "$HOME/.config/autostart"

cat > "$USER_SCRIPT" << 'EOF'
#!/bin/bash
export DISPLAY="${DISPLAY:-:0}"
if command -v setxkbmap >/dev/null 2>&1; then
    setxkbmap -model pc105 -layout it -variant winkeys
fi
if command -v gsettings >/dev/null 2>&1; then
    gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'it+winkeys')]"
    gsettings set org.gnome.desktop.input-sources current 0
    gsettings set org.gnome.desktop.input-sources mru-sources "[('xkb', 'it+winkeys')]"
fi
if command -v ibus >/dev/null 2>&1; then
    ibus engine xkb:it::ita 2>/dev/null || true
fi
EOF
chmod +x "$USER_SCRIPT"

if [[ ! -f "$HOME/.xprofile" ]] || ! grep -q set-italian-keyboard "$HOME/.xprofile" 2>/dev/null; then
    cat >> "$HOME/.xprofile" << EOF

# Tastiera italiana (pc105)
if [ -x "$USER_SCRIPT" ]; then
    "$USER_SCRIPT"
fi
EOF
fi

cat > "$HOME/.config/autostart/set-italian-keyboard.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Set Italian Keyboard
Exec=$USER_SCRIPT
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF

"$USER_SCRIPT"

if [[ "$INSTALL_SYSTEM" -eq 1 ]]; then
    if [[ "$EUID" -ne 0 ]]; then
        echo "Per --system eseguire: sudo $0 --system"
        exit 1
    fi
  cat > /etc/default/keyboard << 'EOF'
# Tastiera italiana - tastiera fisica EU (105 tasti)
XKBMODEL="pc105"
XKBLAYOUT="it"
XKBVARIANT="winkeys"
XKBOPTIONS=""
BACKSPACE=guess
EOF
    if command -v localectl >/dev/null 2>&1; then
        localectl set-x11-keymap it winkeys pc105
        localectl set-keymap it
    fi
    if [[ -f /etc/xrdp/startwm.sh ]] && ! grep -q set-italian-keyboard /etc/xrdp/startwm.sh; then
        sed -i '/^exec \/usr\/bin\/gnome-session/i\
# Tastiera italiana per sessioni xrdp\
if [ -x "'"$HOME"'/.local/bin/set-italian-keyboard.sh" ]; then\
    "'"$HOME"'/.local/bin/set-italian-keyboard.sh"\
fi\
' /etc/xrdp/startwm.sh
    fi
    echo "Configurazione di sistema applicata. Riavvia la sessione grafica o xrdp."
fi

echo "Layout attivo:"
setxkbmap -query 2>/dev/null || true
