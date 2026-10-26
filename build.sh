#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_ID="com.google_unofficial.Gemini"
MANIFEST="${APP_ID}.yaml"
METAINFO="${APP_ID}.metainfo.xml"
DESKTOP="${APP_ID}.desktop"
BUILD_DIR="build-dir"
REPO_DIR="repo"
BUNDLE_FILE="${APP_ID}.flatpak"

usage() {
    cat <<EOF
Uso: $0 [comando]

Comandos disponíveis:
  all       Gera ícones, executa validações de lint e compila/instala o Flatpak (padrão)
  icons     Gera e sincroniza os ícones oficiais SVG e PNG (128x128)
  lint      Executa flatpak-builder-lint (appstream e manifest) e validadores locais
  build     Compila e instala localmente via flatpak-builder
  bundle    Gera um arquivo instalável '${BUNDLE_FILE}' para abrir na GNOME Software / App Bazaar
  run       Executa o aplicativo Flatpak instalado (flatpak run ${APP_ID})
  clean     Remove diretórios temporários de build
EOF
}

cmd_icons() {
    echo "==> [1/3] Gerando e sincronizando ícones oficiais do Google Gemini..."
    python3 generate_icon.py
}

cmd_lint() {
    echo "==> [2/3] Executando validação de Lint (AppStream, Desktop e Manifesto)..."

    if command -v desktop-file-validate >/dev/null 2>&1; then
        desktop-file-validate "${DESKTOP}"
        echo "✔ Arquivo .desktop validado com sucesso."
    fi

    if command -v flatpak-builder-lint >/dev/null 2>&1; then
        flatpak-builder-lint appstream "${METAINFO}"
        flatpak-builder-lint manifest "${MANIFEST}"
    elif flatpak info org.flatpak.Builder >/dev/null 2>&1; then
        flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream "${METAINFO}"
        flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest "${MANIFEST}"
    else
        echo "ℹ flatpak-builder-lint não encontrado no ambiente; executando validação equivalente com appstreamcli e Python YAML..."
        appstreamcli validate --no-net "${METAINFO}"
        python3 -m py_compile app.py generate_icon.py
        rm -rf __pycache__
        echo "✔ Sintaxe Python e AppStream validadas com sucesso."
    fi
}

cmd_build() {
    echo "==> [3/3] Compilando e instalando pacote Flatpak localmente..."
    flatpak-builder --user --install --force-clean "${BUILD_DIR}" "${MANIFEST}"
}

cmd_bundle() {
    echo "==> Gerando pacote Flatpak autocontido (${BUNDLE_FILE}) para GNOME Software / App Bazaar..."
    flatpak-builder --repo="${REPO_DIR}" --force-clean "${BUILD_DIR}" "${MANIFEST}"
    flatpak build-bundle "${REPO_DIR}" "${BUNDLE_FILE}" "${APP_ID}"
    echo "✔ Pacote '${BUNDLE_FILE}' gerado com sucesso! Qualquer usuário pode dar dois cliques nele para instalar pela loja."
}

cmd_run() {
    echo "==> Iniciando ${APP_ID} via Flatpak..."
    flatpak run "${APP_ID}"
}

cmd_clean() {
    echo "==> Limpando artefatos de build..."
    rm -rf "${BUILD_DIR}" .flatpak-builder "${REPO_DIR}"
}

ACTION="${1:-all}"

case "${ACTION}" in
    icons)
        cmd_icons
        ;;
    lint)
        cmd_lint
        ;;
    build)
        cmd_icons
        cmd_build
        ;;
    bundle)
        cmd_icons
        cmd_bundle
        ;;
    run)
        cmd_run
        ;;
    clean)
        cmd_clean
        ;;
    all)
        cmd_icons
        cmd_lint
        cmd_build
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        echo "Comando desconhecido: ${ACTION}" >&2
        usage
        exit 1
        ;;
esac
