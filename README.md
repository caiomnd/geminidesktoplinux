# Gemini Desktop para Linux / GNOME

Aplicativo desktop do Google Gemini para o ecossistema **GNOME** (`GTK 4` + `Libadwaita` + `WebKitGTK 6.0`), com o mesmo design limpo de janela contínua dos aplicativos desktop de **Windows e macOS**, preparado para instalação nas lojas **GNOME Software** e **App Bazaar** (via **Flathub**).

- **Repositório Oficial**: [https://github.com/caiomnd/geminidesktoplinux](https://github.com/caiomnd/geminidesktoplinux)

![Screenshot do Gemini Desktop no GNOME](screenshots/main-dark.png)

---

## Principais Recursos

- **Aparência de App Desktop (Windows / macOS)**: Janela limpa com barra de título contínua (`flat`) integrada ao tema claro/escuro do GNOME, sem barras de endereço ou botões de navegador.
- **Login Direto no Navegador Padrão**: Utiliza a própria interface oficial do Gemini e, ao clicar em **"Fazer login"**, redireciona a autenticação da Conta Google diretamente para o navegador padrão do usuário.
- **Ícone Oficial Sincronizado Automaticamente**: Acompanha o ícone vetorial oficial do Google Gemini e verifica automaticamente atualizações nos servidores da Google.
- **Pronto para GNOME Software / App Bazaar / Flathub**: Metadados AppStream 1.0 validados (`com.google_unofficial.Gemini.metainfo.xml`), arquivo `.desktop` e manifesto Flatpak.

---

## Como Subir para o GitHub e Publicar no Flathub

Use o script automatizado [`flathub-publish.sh`](./flathub-publish.sh):

```bash
# 1. Inicializa o Git, cria a tag v1.2.0 e faz push para https://github.com/caiomnd/geminidesktoplinux
./flathub-publish.sh push-github

# 2. Configura o org.flatpak.Builder e compila/valida o pacote Flatpak localmente
./flathub-publish.sh setup
./flathub-publish.sh build
./flathub-publish.sh lint

# 3. Gera o manifesto final com o hash do commit do seu GitHub para abrir o PR no Flathub
./flathub-publish.sh prepare-pr
```

---

## Execução Rápida Local

```bash
./run.sh
```
