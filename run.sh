#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_ID="com.google_unofficial.Gemini"
APP_DIR="$(pwd)"
LOCAL_SHARE="${HOME}/.local/share"
LOCAL_BIN="${HOME}/.local/bin"

echo "==> Preparando ambiente e integração com o GNOME..."

# 1. Garante que o ícone oficial do Google Gemini esteja gerado e sincronizado com a Google
python3 "${APP_DIR}/generate_icon.py"

# 2. Instala o executável e atalho .desktop localmente (~/.local) para que o GNOME Shell reconheça o ícone e o app
mkdir -p "${LOCAL_BIN}"
mkdir -p "${LOCAL_SHARE}/applications"
mkdir -p "${LOCAL_SHARE}/icons/hicolor/128x128/apps"
mkdir -p "${LOCAL_SHARE}/icons/hicolor/scalable/apps"

ln -sf "${APP_DIR}/app.py" "${LOCAL_BIN}/gemini-desktop"
chmod +x "${APP_DIR}/app.py"

cp -f "${APP_DIR}/icons/128x128/${APP_ID}.png" "${LOCAL_SHARE}/icons/hicolor/128x128/apps/${APP_ID}.png"
cp -f "${APP_DIR}/icons/scalable/${APP_ID}.svg" "${LOCAL_SHARE}/icons/hicolor/scalable/apps/${APP_ID}.svg"

# Cria o .desktop apontando para o caminho absoluto do binário local para funcionar no menu do GNOME
sed "s|^Exec=.*|Exec=${LOCAL_BIN}/gemini-desktop|g" "${APP_DIR}/${APP_ID}.desktop" > "${LOCAL_SHARE}/applications/${APP_ID}.desktop"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${LOCAL_SHARE}/icons/hicolor" >/dev/null 2>&1 || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${LOCAL_SHARE}/applications" >/dev/null 2>&1 || true
fi

# 3. Se o pacote Flatpak estiver instalado e o usuário passar --flatpak, inicia via Flatpak
if [ "${1:-}" = "--flatpak" ] && flatpak info "${APP_ID}" >/dev/null 2>&1; then
    echo "==> Iniciando ${APP_ID} via Flatpak..."
    exec flatpak run "${APP_ID}"
fi

# 4. Inicia o aplicativo nativamente com PyGObject (GTK 4 + Libadwaita + WebKitGTK 6.0)
echo "==> Subindo aplicativo Gemini Desktop (${APP_ID})..."
export WEBKIT_FORCE_SANDBOX=0
exec python3 "${APP_DIR}/app.py" "$@"
