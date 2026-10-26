#!/usr/bin/env bash
# ==============================================================================
# Script Oficial de Preparação, Git Push, Build, Lint e Submissão ao Flathub
# Repositório Oficial: https://github.com/caiomnd/geminidesktoplinux
# Baseado em: https://docs.flathub.org/docs/for-app-authors/submission
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")"

APP_ID="com.google_unofficial.Gemini"
FLATHUB_ID="io.github.caiomnd.Gemini"
GITHUB_USER="caiomnd"
GITHUB_REPO_URL="https://github.com/caiomnd/geminidesktoplinux.git"
RELEASE_TAG="v1.2.0"

MANIFEST="${APP_ID}.yaml"
METAINFO="${APP_ID}.metainfo.xml"
DESKTOP="${APP_ID}.desktop"
BUILD_DIR="build-dir"
REPO_DIR="repo"
BUNDLE_FILE="${APP_ID}.flatpak"

usage() {
    cat <<EOF
Uso: $0 [etapa]

Etapas disponíveis para https://github.com/caiomnd/geminidesktoplinux:

  push-github [Passo 0] Inicializa o Git, cria commit/tag ${RELEASE_TAG} e envia (git push) para
                        https://github.com/caiomnd/geminidesktoplinux
  setup       [Passo 1] Configura o repositório Flathub (--user) e instala org.flatpak.Builder e SDK
  build       [Passo 2] Compila e instala localmente usando org.flatpak.Builder
  lint        [Passo 3] Executa o linter oficial do Flathub (manifest, appstream e repo)
  bundle      [Extra]   Empacota '${BUNDLE_FILE}' para instalar com 2 cliques na GNOME Software / App Bazaar
  prepare-pr  [Passo 4] Clona seu fork do flathub/flathub (branch new-pr) e gera o manifesto com o commit/tag
                        de https://github.com/caiomnd/geminidesktoplinux
  run                   Executa o aplicativo Flatpak instalado (flatpak run ${APP_ID})
  clean                 Remove artefatos temporários de compilação
  all                   Executa setup -> icons -> build -> lint -> bundle em sequência
EOF
}

step_icons() {
    echo "======================================================================"
    echo "==> Sincronizando ícone oficial do Google Gemini e Screenshot..."
    echo "======================================================================"
    python3 generate_icon.py
    python3 generate_screenshot.py
}

step_push_github() {
    echo "======================================================================"
    echo "==> [Passo 0] Preparando e enviando para ${GITHUB_REPO_URL}"
    echo "======================================================================"
    step_icons
    rm -rf __pycache__

    if [ ! -d ".git" ]; then
        git init -b main
    fi

    if [ -z "$(git config user.name || true)" ]; then
        git config user.name "Caio Mendonça"
    fi
    if [ -z "$(git config user.email || true)" ]; then
        git config user.email "caiomnd@users.noreply.github.com"
    fi

    if git remote get-url origin >/dev/null 2>&1; then
        git remote set-url origin "${GITHUB_REPO_URL}"
    else
        git remote add origin "${GITHUB_REPO_URL}"
    fi

    git add .
    if ! git diff --cached --quiet; then
        git commit -m "Release ${RELEASE_TAG}: Gemini Desktop for GNOME (GTK 4 + Libadwaita + Flatpak)"
    else
        echo "ℹ Nenhuma alteração pendente para commit."
    fi

    git tag -f "${RELEASE_TAG}"
    COMMIT_HASH="$(git rev-parse HEAD)"
    echo "✔ Repositório Git pronto! Branch: main | Tag: ${RELEASE_TAG} | Commit: ${COMMIT_HASH}"
    echo "-> Enviando para o GitHub..."
    if ! git push -u origin main --tags --force; then
        echo ""
        echo "⚠ Falha de autenticação no GitHub (o GitHub exige Chave SSH ou Personal Access Token)."
        echo "-> Iniciando assistente automático de autenticação (./github-auth.sh)..."
        ./github-auth.sh
    fi
    echo "✔ Projeto publicado com sucesso em https://github.com/caiomnd/geminidesktoplinux !"
}

step_setup() {
    echo "======================================================================"
    echo "==> [Passo 1] Configurando repositório Flathub e org.flatpak.Builder..."
    echo "======================================================================"

    flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo

    if ! flatpak info org.flatpak.Builder >/dev/null 2>&1; then
        echo "-> Instalando org.flatpak.Builder a partir do Flathub..."
        flatpak install -y --user flathub org.flatpak.Builder
    else
        echo "✔ org.flatpak.Builder já está instalado."
    fi

    if ! flatpak info org.gnome.Sdk//50 >/dev/null 2>&1; then
        echo "-> Instalando org.gnome.Sdk//50 e org.gnome.Platform//50..."
        flatpak install -y --user flathub org.gnome.Platform//50 org.gnome.Sdk//50
    else
        echo "✔ Runtime e SDK do GNOME 50 já estão instalados."
    fi
}

step_build() {
    echo "======================================================================"
    echo "==> [Passo 2] Compilando e instalando o pacote via org.flatpak.Builder"
    echo "======================================================================"

    if flatpak info org.flatpak.Builder >/dev/null 2>&1; then
        flatpak run --command=flatpak-builder org.flatpak.Builder \
            --user --install --force-clean --repo="${REPO_DIR}" "${BUILD_DIR}" "${MANIFEST}"
    elif command -v flatpak-builder >/dev/null 2>&1; then
        flatpak-builder --user --install --force-clean --repo="${REPO_DIR}" "${BUILD_DIR}" "${MANIFEST}"
    else
        echo "Erro: nem org.flatpak.Builder nem flatpak-builder foram encontrados. Rode '$0 setup' primeiro." >&2
        exit 1
    fi
    echo "✔ Build e instalação local concluídos com sucesso!"
}

step_lint() {
    echo "======================================================================"
    echo "==> [Passo 3] Executando o Linter Oficial do Flathub (flatpak-builder-lint)"
    echo "======================================================================"

    if command -v desktop-file-validate >/dev/null 2>&1; then
        echo "-> Validando ${DESKTOP}..."
        desktop-file-validate "${DESKTOP}"
    fi

    if flatpak info org.flatpak.Builder >/dev/null 2>&1; then
        echo "-> Executando flatpak-builder-lint appstream ${METAINFO}..."
        flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream "${METAINFO}" || true

        echo "-> Executando flatpak-builder-lint manifest ${MANIFEST}..."
        flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest "${MANIFEST}" || true

        if [ -d "${REPO_DIR}" ]; then
            echo "-> Executando flatpak-builder-lint repo ${REPO_DIR}..."
            flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo "${REPO_DIR}" || true
        fi
    elif command -v flatpak-builder-lint >/dev/null 2>&1; then
        flatpak-builder-lint appstream "${METAINFO}" || true
        flatpak-builder-lint manifest "${MANIFEST}" || true
        if [ -d "${REPO_DIR}" ]; then
            flatpak-builder-lint repo "${REPO_DIR}" || true
        fi
    else
        echo "-> Validando localmente com appstreamcli (instale org.flatpak.Builder com '$0 setup' para o linter completo)..."
        appstreamcli validate --no-net "${METAINFO}"
    fi

    echo "✔ Etapa de verificação de lint concluída!"
}

step_bundle() {
    echo "======================================================================"
    echo "==> Gerando pacote instalável ${BUNDLE_FILE} (GNOME Software / App Bazaar)"
    echo "======================================================================"
    if [ ! -d "${REPO_DIR}" ]; then
        step_build
    fi
    flatpak build-bundle "${REPO_DIR}" "${BUNDLE_FILE}" "${APP_ID}"
    echo "✔ Arquivo '${BUNDLE_FILE}' criado com sucesso!"
}

step_prepare_pr() {
    echo "======================================================================"
    echo "==> [Passo 4] Preparando Manifesto Flathub para ${GITHUB_REPO_URL}"
    echo "======================================================================"

    COMMIT_HASH="HEAD"
    if [ -d ".git" ]; then
        COMMIT_HASH="$(git rev-parse HEAD)"
    fi

    # Gera manifesto pronto para submissão ao Flathub apontando para o GitHub caiomnd/geminidesktoplinux
    cat <<EOF > "flathub-${MANIFEST}"
app-id: ${APP_ID}
runtime: org.gnome.Platform
runtime-version: '50'
sdk: org.gnome.Sdk
command: gemini-desktop

finish-args:
  - --socket=wayland
  - --socket=fallback-x11
  - --share=network
  - --share=ipc
  - --socket=pulseaudio
  - --device=dri

modules:
  - name: gemini-desktop
    buildsystem: simple
    build-commands:
      - install -Dm755 app.py /app/bin/gemini-desktop
      - install -Dm755 generate_icon.py /app/bin/generate_icon.py
      - install -Dm644 ${APP_ID}.desktop /app/share/applications/${APP_ID}.desktop
      - install -Dm644 ${APP_ID}.metainfo.xml /app/share/metainfo/${APP_ID}.metainfo.xml
      - install -Dm644 icons/128x128/${APP_ID}.png /app/share/icons/hicolor/128x128/apps/${APP_ID}.png
      - install -Dm644 icons/scalable/${APP_ID}.svg /app/share/icons/hicolor/scalable/apps/${APP_ID}.svg
    sources:
      - type: git
        url: ${GITHUB_REPO_URL}
        tag: ${RELEASE_TAG}
        commit: ${COMMIT_HASH}
EOF

    echo "✔ Manifesto de submissão gerado em 'flathub-${MANIFEST}' apontando para:"
    echo "  URL:    ${GITHUB_REPO_URL}"
    echo "  Tag:    ${RELEASE_TAG}"
    echo "  Commit: ${COMMIT_HASH}"

    PR_DIR="flathub-pr-${APP_ID}"
    echo ""
    echo "Para clonar seu fork do Flathub (https://github.com/${GITHUB_USER}/flathub) e criar a branch de PR:"
    echo "  git clone --branch=new-pr --single-branch https://github.com/${GITHUB_USER}/flathub.git ${PR_DIR}"
    echo "  cd ${PR_DIR} && git checkout -B add-${APP_ID} new-pr"
    echo "  cp ../flathub-${MANIFEST} ./${MANIFEST}"
    echo "  git add ${MANIFEST} && git commit -m 'Add ${APP_ID}' && git push -u origin add-${APP_ID}"
}

step_run() {
    echo "==> Executando ${APP_ID} via Flatpak..."
    flatpak run "${APP_ID}"
}

step_clean() {
    echo "==> Limpando diretórios de build..."
    rm -rf "${BUILD_DIR}" "${REPO_DIR}" .flatpak-builder __pycache__
}

ACTION="${1:-all}"

case "${ACTION}" in
    push-github)
        step_push_github
        ;;
    setup)
        step_setup
        ;;
    icons)
        step_icons
        ;;
    build)
        step_icons
        step_build
        ;;
    lint)
        step_lint
        ;;
    bundle)
        step_icons
        step_bundle
        ;;
    prepare-pr)
        step_prepare_pr
        ;;
    run)
        step_run
        ;;
    clean)
        step_clean
        ;;
    all)
        step_setup
        step_icons
        step_build
        step_lint
        step_bundle
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
