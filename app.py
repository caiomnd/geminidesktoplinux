#!/usr/bin/env python3
"""
Gemini Desktop para GNOME (com.google_unofficial.Gemini)
- Aparência idêntica ao aplicativo Desktop oficial (Windows / macOS): janela limpa e sem
  controles de navegador (sem barra de endereço, sem botões de voltar/avançar/recarregar),
  com HeaderBar minimalista e contínua na mesma cor de fundo do Gemini.
- Integração nativa de pacote e instalação para as lojas GNOME Software e App Bazaar (Flathub).
- Utiliza o próprio login oficial do Gemini, mas ao clicar em Fazer Login (accounts.google.com),
  encaminha automaticamente o usuário para o navegador padrão do sistema.
- Ícone oficial do Google Gemini sincronizado automaticamente a partir dos servidores da Google.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("WebKit", "6.0")

from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, Gtk, WebKit  # noqa: E402

APP_ID = "com.google_unofficial.Gemini"
APP_NAME = "Gemini"
APP_VERSION = "1.2.0"
GEMINI_URL = "https://gemini.google.com/app"

# Domínios de login da Conta Google que devem ser encaminhados ao navegador padrão
AUTH_HOSTS = (
    "accounts.google.com",
    "accounts.youtube.com",
)

# Estilo CSS para deixar a janela idêntica ao app desktop do Windows/macOS:
# HeaderBar completamente flat e integrada ao fundo do Gemini (#131314 no escuro, #f8fafd no claro),
# sem bordas divisórias nem botões de navegador.
DESKTOP_APP_CSS = """
window.gemini-desktop-window {
    background-color: #f8fafd;
}

window.gemini-desktop-window.dark-mode {
    background-color: #131314;
}

headerbar.gemini-clean-header {
    background: transparent;
    background-color: #f8fafd;
    border-bottom: none;
    box-shadow: none;
    min-height: 36px;
    padding: 0 8px;
}

window.gemini-desktop-window.dark-mode headerbar.gemini-clean-header {
    background-color: #131314;
}

.gemini-header-title {
    font-weight: 600;
    font-size: 0.92rem;
    opacity: 0.78;
}
"""


class GeminiWindow(Adw.ApplicationWindow):
    """
    Janela estilo Desktop App oficial (Windows/macOS):
    Sem botões de navegador, apenas os controles de janela nativos do GNOME (minimizar/maximizar/fechar)
    integrados de forma limpa na barra de título flat.
    """

    def __init__(self, application: Adw.Application) -> None:
        super().__init__(
            application=application,
            title=APP_NAME,
            default_width=1200,
            default_height=820,
        )
        self.set_size_request(400, 560)
        self.set_icon_name(APP_ID)
        self.add_css_class("gemini-desktop-window")

        # ToastOverlay para avisar de forma sutil quando o login é aberto no navegador padrão
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        self.toolbar_view = Adw.ToolbarView()
        self.toast_overlay.set_child(self.toolbar_view)

        # HeaderBar limpa estilo macOS/Windows Titlebar (sem botões de navegador)
        self.header_bar = Adw.HeaderBar()
        self.header_bar.add_css_class("gemini-clean-header")
        self.header_bar.add_css_class("flat")

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_box.set_valign(Gtk.Align.CENTER)

        app_icon = Gtk.Image.new_from_icon_name(APP_ID)
        app_icon.set_pixel_size(18)
        title_box.append(app_icon)

        self.title_label = Gtk.Label(label=APP_NAME)
        self.title_label.add_css_class("gemini-header-title")
        title_box.append(self.title_label)

        self.header_bar.set_title_widget(title_box)
        self.toolbar_view.add_top_bar(self.header_bar)

        # WebView configurado com a interface oficial do Google Gemini
        self.webview = self._create_webview()
        self.toolbar_view.set_content(self.webview)

        # Atalhos de teclado discretos de aplicativo desktop
        self._setup_shortcuts()

        # Sincroniza Modo Claro / Escuro com o GNOME
        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.connect("notify::dark", self._on_dark_mode_changed)
        self._apply_color_scheme()

        # Atualiza o ícone oficial do Google Gemini em background caso a Google o atualize
        threading.Thread(target=self._background_icon_sync, daemon=True).start()

        # Carrega diretamente o app do Gemini
        self.webview.load_uri(GEMINI_URL)

    def _create_webview(self) -> WebKit.WebView:
        data_dir = Path(GLib.get_user_data_dir()) / APP_ID / "webkit"
        cache_dir = Path(GLib.get_user_cache_dir()) / APP_ID / "webkit"
        data_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        network_session = WebKit.NetworkSession.new(str(data_dir), str(cache_dir))
        network_session.set_persistent_credential_storage_enabled(True)

        website_data_manager = network_session.get_website_data_manager()
        if website_data_manager is not None:
            website_data_manager.set_favicons_enabled(True)

        cookie_manager = network_session.get_cookie_manager()
        cookies_path = data_dir / "cookies.sqlite"
        cookie_manager.set_persistent_storage(
            str(cookies_path),
            WebKit.CookiePersistentStorage.SQLITE,
        )
        cookie_manager.set_accept_policy(WebKit.CookieAcceptPolicy.ALWAYS)

        settings = WebKit.Settings()
        settings.set_enable_javascript(True)
        settings.set_enable_webgl(True)
        settings.set_enable_webaudio(True)
        settings.set_enable_media(True)
        settings.set_enable_media_stream(True)
        settings.set_enable_mediasource(True)
        settings.set_enable_2d_canvas_acceleration(True)
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_back_forward_navigation_gestures(False)
        # Desativa menu de contexto de navegador ("Inspecionar elemento", "Voltar", etc.) para parecer 100% app desktop
        settings.set_enable_developer_extras(False)
        settings.set_hardware_acceleration_policy(
            WebKit.HardwareAccelerationPolicy.ALWAYS
        )

        settings.set_user_agent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.4 Safari/605.1.15"
        )

        webview = WebKit.WebView(
            network_session=network_session,
            settings=settings,
        )
        webview.set_hexpand(True)
        webview.set_vexpand(True)

        webview.connect("load-changed", self._on_load_changed)
        webview.connect("notify::favicon", self._on_favicon_changed)
        webview.connect("decide-policy", self._on_decide_policy)
        webview.connect("create", self._on_create_new_web_view)
        webview.connect("permission-request", self._on_permission_request)
        webview.connect("context-menu", self._on_context_menu)

        return webview

    def _setup_shortcuts(self) -> None:
        reload_action = Gio.SimpleAction.new("reload", None)
        reload_action.connect("activate", lambda *_: self.webview.reload())
        self.add_action(reload_action)

    def _on_context_menu(
        self,
        _webview: WebKit.WebView,
        context_menu: WebKit.ContextMenu,
        _hit_test_result: WebKit.HitTestResult,
    ) -> bool:
        """
        Filtra o menu de clique direito para remover opções de navegador (Voltar, Avançar, Recarregar, Baixar link),
        mantendo apenas Copiar, Colar, Recortar e Selecionar Tudo, como nos apps desktop de Windows/macOS.
        """
        allowed_actions = {
            WebKit.ContextMenuAction.COPY,
            WebKit.ContextMenuAction.CUT,
            WebKit.ContextMenuAction.PASTE,
            WebKit.ContextMenuAction.SELECT_ALL,
            WebKit.ContextMenuAction.UNDO,
            WebKit.ContextMenuAction.REDO,
            WebKit.ContextMenuAction.SPELLING_GUESS,
            WebKit.ContextMenuAction.NO_ACTION,
        }
        items = list(context_menu.get_items())
        for item in items:
            if item.get_stock_action() not in allowed_actions:
                context_menu.remove(item)
        return False

    def _apply_color_scheme(self) -> None:
        """Sincroniza perfeitamente o fundo da janela, HeaderBar e WebView com o tema do sistema."""
        is_dark = self.style_manager.get_dark()
        bg_rgba = Gdk.RGBA()
        if is_dark:
            self.add_css_class("dark-mode")
            bg_rgba.parse("#131314")
        else:
            self.remove_css_class("dark-mode")
            bg_rgba.parse("#f8fafd")
        self.webview.set_background_color(bg_rgba)

        scheme = "dark" if is_dark else "light"
        js_sync = f"""
        (function() {{
            document.documentElement.style.colorScheme = '{scheme}';
        }})();
        """
        self.webview.evaluate_javascript(js_sync, -1, None, None, None, None, None)

    def _on_dark_mode_changed(self, _style_manager: Adw.StyleManager, _pspec: object) -> None:
        self._apply_color_scheme()

    def _on_load_changed(self, _webview: WebKit.WebView, load_event: WebKit.LoadEvent) -> None:
        if load_event == WebKit.LoadEvent.FINISHED:
            self._apply_color_scheme()

    def _open_in_default_browser(self, uri: str, is_auth: bool = False) -> None:
        """Encaminha a URL diretamente para o navegador padrão do usuário."""
        try:
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception:
            Gtk.UriLauncher.new(uri).launch(self, None, None, None)

        if is_auth:
            toast = Adw.Toast.new("Redirecionando login para o seu navegador padrão…")
            toast.set_timeout(4)
            self.toast_overlay.add_toast(toast)

    def _on_create_new_web_view(
        self,
        _webview: WebKit.WebView,
        navigation_action: WebKit.NavigationAction,
    ) -> Gtk.Widget | None:
        """
        Captura popups window.open() (usados pelo botão Sign In do Gemini ou links externos)
        e encaminha diretamente para o navegador padrão do usuário.
        """
        request = navigation_action.get_request()
        uri = request.get_uri() if request else ""
        if uri:
            is_auth = self._is_auth_uri(uri)
            if self._is_gemini_domain(uri) and not is_auth:
                self.webview.load_uri(uri)
            else:
                self._open_in_default_browser(uri, is_auth=is_auth)
        return None

    def _on_decide_policy(
        self,
        _webview: WebKit.WebView,
        decision: WebKit.PolicyDecision,
        decision_type: WebKit.PolicyDecisionType,
    ) -> bool:
        """
        Intercepta cliques em 'Fazer Login' (Sign in) no próprio Gemini e encaminha
        para o navegador padrão do usuário.
        """
        if decision_type in (
            WebKit.PolicyDecisionType.NAVIGATION_ACTION,
            WebKit.PolicyDecisionType.NEW_WINDOW_ACTION,
        ):
            nav_action = decision.get_navigation_action()
            request = nav_action.get_request()
            uri = request.get_uri() if request else ""
            if not uri or uri.startswith(("javascript:", "about:", "data:", "blob:")):
                return False

            # 1. Ao clicar em Login (accounts.google.com), abre no navegador padrão do usuário
            if self._is_auth_uri(uri):
                self._open_in_default_browser(uri, is_auth=True)
                decision.ignore()
                return True

            # 2. Solicitação de nova janela (target="_blank")
            if decision_type == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
                if self._is_gemini_domain(uri):
                    self.webview.load_uri(uri)
                else:
                    self._open_in_default_browser(uri, is_auth=False)
                decision.ignore()
                return True

            # 3. Clique em link externo fora do Gemini abre no navegador padrão
            if (
                decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION
                and nav_action.get_navigation_type() == WebKit.NavigationType.LINK_CLICKED
                and not self._is_gemini_domain(uri)
            ):
                self._open_in_default_browser(uri, is_auth=False)
                decision.ignore()
                return True

        return False

    @staticmethod
    def _is_auth_uri(uri: str) -> bool:
        """Identifica o fluxo de login da Conta Google acionado pelo botão de login do Gemini."""
        parsed = urlparse(uri)
        host = (parsed.hostname or "").lower()
        path = (parsed.path or "").lower()

        if any(host == auth_host or host.endswith(f".{auth_host}") for auth_host in AUTH_HOSTS):
            # Ignora iframes ocultos de verificação silenciosa de sessão para não disparar abas sem clique
            silent_paths = (
                "/checkconnection",
                "/rotatecookies",
                "/listaccounts",
                "/passive",
                "/iframe",
            )
            if any(sp in path for sp in silent_paths):
                return False
            return True

        if host.endswith(".google.com") and any(
            segment in path
            for segment in ("/servicelogin", "/signin", "/o/oauth2", "/accountchooser")
        ):
            return True

        return False

    @staticmethod
    def _is_gemini_domain(uri: str) -> bool:
        parsed = urlparse(uri)
        host = (parsed.hostname or "").lower()
        allowed_hosts = (
            "gemini.google.com",
            "bard.google.com",
            "ogs.google.com",
            "www.gstatic.com",
            "apis.google.com",
        )
        return any(host == h or host.endswith(f".{h}") for h in allowed_hosts)

    def _on_permission_request(
        self,
        _webview: WebKit.WebView,
        request: WebKit.PermissionRequest,
    ) -> bool:
        """Permite uso de microfone/áudio e notificações nativas para recursos de voz do Gemini."""
        if isinstance(
            request,
            (
                WebKit.UserMediaPermissionRequest,
                WebKit.MediaKeySystemPermissionRequest,
                WebKit.NotificationPermissionRequest,
            ),
        ):
            request.allow()
            return True
        return False

    def _background_icon_sync(self) -> None:
        """Verifica em background se a Google atualizou o ícone oficial do Gemini."""
        try:
            import generate_icon

            if generate_icon.generate_icons(check_remote=True):
                GLib.idle_add(self._reload_window_icon)
        except Exception:
            pass

    def _reload_window_icon(self) -> bool:
        display = Gdk.Display.get_default()
        if display is not None:
            icon_theme = Gtk.IconTheme.get_for_display(display)
            local_icons = Path.home() / ".local" / "share" / "icons"
            if local_icons.exists():
                icon_theme.add_search_path(str(local_icons))
        self.set_icon_name(APP_ID)
        return GLib.SOURCE_REMOVE

    def _on_favicon_changed(self, webview: WebKit.WebView, _pspec: object) -> None:
        favicon_texture = webview.get_favicon()
        if favicon_texture is None:
            return
        try:
            if favicon_texture.get_width() >= 64 and favicon_texture.get_height() >= 64:
                png_bytes = favicon_texture.save_to_png_bytes().get_data()
                if png_bytes:
                    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
                    loader.set_size(128, 128)
                    loader.write(png_bytes)
                    loader.close()
                    pixbuf = loader.get_pixbuf()
                    if pixbuf is not None:
                        local_png = (
                            Path.home()
                            / ".local"
                            / "share"
                            / "icons"
                            / "hicolor"
                            / "128x128"
                            / "apps"
                            / f"{APP_ID}.png"
                        )
                        local_png.parent.mkdir(parents=True, exist_ok=True)
                        pixbuf.savev(str(local_png), "png", [], [])
        except Exception:
            pass


class GeminiApplication(Adw.Application):
    """Aplicação principal com integração nativa ao desktop GNOME."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        GLib.set_application_name(APP_NAME)
        GLib.set_prgname(APP_ID)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)

        display = Gdk.Display.get_default()
        if display is not None:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_string(DESKTOP_APP_CSS)
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

            icon_theme = Gtk.IconTheme.get_for_display(display)
            local_icons = Path.home() / ".local" / "share" / "icons"
            if local_icons.exists():
                icon_theme.add_search_path(str(local_icons))
            project_icons = Path(__file__).resolve().parent / "icons"
            if project_icons.exists():
                icon_theme.add_search_path(str(project_icons))

        Gtk.Window.set_default_icon_name(APP_ID)

        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)

        self.set_accels_for_action("app.quit", ["<primary>q", "<primary>w"])
        self.set_accels_for_action("win.reload", ["<primary>r", "F5"])

    def do_activate(self) -> None:
        win = self.props.active_window
        if not win:
            win = GeminiWindow(application=self)
        win.present()


def main() -> int:
    os.environ.setdefault("WEBKIT_FORCE_SANDBOX", "0")
    app = GeminiApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
