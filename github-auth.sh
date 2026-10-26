#!/usr/bin/env bash
# ==============================================================================
# Assistente de Autenticação e Push para o GitHub (SSH ou Personal Access Token)
# Repositório: https://github.com/caiomnd/geminidesktoplinux
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")"

GITHUB_USER="caiomnd"
REPO_NAME="geminidesktoplinux"
SSH_KEY_PATH="${HOME}/.ssh/id_ed25519"

echo "======================================================================"
echo "  Configuração de Autenticação do GitHub para ${GITHUB_USER}/${REPO_NAME}"
echo "======================================================================"
echo "O GitHub não aceita mais a senha normal da conta no terminal."
echo "Escolha como deseja autenticar:"
echo ""
echo "  1) Chave SSH (Recomendado - mais seguro, não pede senha novamente)"
echo "  2) Token de Acesso Pessoal (PAT - começa com 'ghp_' ou 'github_pat_')"
echo ""
read -r -p "Digite 1 ou 2 [Padrão: 1]: " AUTH_CHOICE
AUTH_CHOICE="${AUTH_CHOICE:-1}"

if [ "${AUTH_CHOICE}" = "1" ]; then
    mkdir -p "${HOME}/.ssh"
    chmod 700 "${HOME}/.ssh"

    if [ ! -f "${SSH_KEY_PATH}" ]; then
        echo "==> Gerando nova chave SSH Ed25519..."
        ssh-keygen -t ed25519 -C "caiomnd@users.noreply.github.com" -f "${SSH_KEY_PATH}" -N ""
    fi

    PUB_KEY="$(cat "${SSH_KEY_PATH}.pub")"

    # Copia automaticamente para a área de transferência via Gdk (GTK 4) se houver sessão gráfica
    python3 -c "
import gi
gi.require_version('Gdk', '4.0')
from gi.repository import Gdk, GLib
display = Gdk.Display.get_default()
if display:
    cb = display.get_clipboard()
    cb.set('''${PUB_KEY}''')
" 2>/dev/null || true

    echo ""
    echo "======================================================================"
    echo "COPIE A CHAVE SSH PÚBLICA ABAIXO:"
    echo "----------------------------------------------------------------------"
    echo "${PUB_KEY}"
    echo "----------------------------------------------------------------------"
    echo "==> Abrindo a página 'New SSH Key' do GitHub no seu navegador padrão..."
    xdg-open "https://github.com/settings/ssh/new" >/dev/null 2>&1 || true
    echo ""
    echo "No navegador que abriu:"
    echo "  1. Em 'Title', digite: Meu Linux GNOME"
    echo "  2. Em 'Key', cole a chave acima (começa com ssh-ed25519...)"
    echo "  3. Clique no botão verde 'Add SSH key'"
    echo "======================================================================"
    read -r -p "Pressione [ENTER] aqui no terminal assim que tiver clicado em 'Add SSH key' no navegador..."

    # Configura o remote para usar SSH e adiciona github.com ao known_hosts
    ssh-keyscan -t ed25519 github.com >> "${HOME}/.ssh/known_hosts" 2>/dev/null || true
    git remote set-url origin "git@github.com:${GITHUB_USER}/${REPO_NAME}.git"

    echo "==> Enviando projeto para git@github.com:${GITHUB_USER}/${REPO_NAME}.git..."
    git push -u origin main --tags --force
    echo "✔ Sucesso! O projeto foi enviado via SSH para https://github.com/${GITHUB_USER}/${REPO_NAME}"

elif [ "${AUTH_CHOICE}" = "2" ]; then
    echo ""
    echo "==> Abrindo a página de criação de Token do GitHub no seu navegador padrão..."
    echo "    (Marque a caixa 'repo' e clique em 'Generate token' no final da página)"
    xdg-open "https://github.com/settings/tokens/new?description=GeminiDesktopLinux&scopes=repo,workflow" >/dev/null 2>&1 || true
    echo ""
    read -r -s -p "Cole aqui o Token gerado (ghp_...) e pressione [ENTER]: " GH_TOKEN
    echo ""

    if [ -z "${GH_TOKEN}" ]; then
        echo "Erro: Nenhum token informado." >&2
        exit 1
    fi

    git config credential.helper store
    git remote set-url origin "https://${GITHUB_USER}:${GH_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"

    echo "==> Enviando projeto para https://github.com/${GITHUB_USER}/${REPO_NAME}..."
    git push -u origin main --tags --force

    # Remove o token explícito da URL após salvar no credential helper
    git remote set-url origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    echo "✔ Sucesso! O projeto foi enviado para https://github.com/${GITHUB_USER}/${REPO_NAME}"
else
    echo "Opção inválida." >&2
    exit 1
fi
