#!/usr/bin/env python3
"""
Gera a imagem de captura de tela (screenshots/main-dark.png - 1200x820)
exigida pelo AppStream / Flathub para a GNOME Software e App Bazaar.
"""

from pathlib import Path
import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

SCREENSHOT_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="820" viewBox="0 0 1200 820">
  <defs>
    <linearGradient id="geminiTextGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#4e82ee"/>
      <stop offset="50%" stop-color="#9b72cb"/>
      <stop offset="100%" stop-color="#d96570"/>
    </linearGradient>
    <radialGradient id="sparkleGrad" cx="25%" cy="80%" r="90%">
      <stop offset="0%" stop-color="#1b72e8"/>
      <stop offset="40%" stop-color="#4e82ee"/>
      <stop offset="70%" stop-color="#9b72cb"/>
      <stop offset="100%" stop-color="#d96570"/>
    </radialGradient>
  </defs>

  <!-- Fundo da janela estilo GNOME Dark (#131314) -->
  <rect width="1200" height="820" rx="16" fill="#131314" stroke="#2d2e30" stroke-width="2"/>

  <!-- HeaderBar minimalista Flat -->
  <rect x="2" y="2" width="1196" height="44" rx="14" fill="#131314"/>

  <!-- Ícone e título centralizados na HeaderBar -->
  <g transform="translate(555, 13) scale(0.75)">
    <path fill="url(#sparkleGrad)"
          d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.93a12.3 12.3 0 0 1 3.81 2.58q2.19 1.62 2.55 3.81z"/>
  </g>
  <text x="582" y="28" fill="#c4c7c5" font-family="Cantarell, sans-serif" font-size="15" font-weight="bold">Gemini</text>

  <!-- Botões de controle de janela GNOME no canto superior direito -->
  <circle cx="1115" cy="24" r="11" fill="#282a2c"/>
  <rect x="1110" y="26" width="10" height="1.8" fill="#e3e3e3"/>
  <circle cx="1145" cy="24" r="11" fill="#282a2c"/>
  <rect x="1140" y="19" width="10" height="10" fill="none" stroke="#e3e3e3" stroke-width="1.6"/>
  <circle cx="1175" cy="24" r="11" fill="#282a2c"/>
  <path d="M1171 20 L1179 28 M1179 20 L1171 28" stroke="#e3e3e3" stroke-width="1.8"/>

  <!-- Barra lateral recolhível do Gemini -->
  <rect x="2" y="46" width="260" height="772" fill="#1e1f20"/>
  <rect x="20" y="68" width="140" height="36" rx="18" fill="#282a2c"/>
  <text x="48" y="91" fill="#e3e3e3" font-family="Cantarell, sans-serif" font-size="14" font-weight="bold">+ Nova conversa</text>

  <text x="24" y="138" fill="#8e918f" font-family="Cantarell, sans-serif" font-size="12" font-weight="bold">Recentes</text>
  <rect x="14" y="152" width="232" height="34" rx="17" fill="#004a77"/>
  <text x="30" y="174" fill="#c2e7ff" font-family="Cantarell, sans-serif" font-size="13">Arquitetura GNOME e Flatpak</text>
  <text x="30" y="212" fill="#c4c7c5" font-family="Cantarell, sans-serif" font-size="13">Automação em Python no Linux</text>
  <text x="30" y="246" fill="#c4c7c5" font-family="Cantarell, sans-serif" font-size="13">Otimização de containers</text>

  <!-- Saudação Central do Gemini -->
  <text x="420" y="260" fill="url(#geminiTextGrad)" font-family="Cantarell, sans-serif" font-size="44" font-weight="bold">Olá, usuário GNOME</text>
  <text x="420" y="312" fill="#444746" font-family="Cantarell, sans-serif" font-size="40" font-weight="bold">Como posso ajudar hoje?</text>

  <!-- Cards de sugestão -->
  <rect x="420" y="365" width="200" height="140" rx="16" fill="#1e1f20"/>
  <text x="438" y="400" fill="#e3e3e3" font-family="Cantarell, sans-serif" font-size="14">Explicar o funcionamento</text>
  <text x="438" y="422" fill="#e3e3e3" font-family="Cantarell, sans-serif" font-size="14">do Wayland no GNOME</text>

  <rect x="636" y="365" width="200" height="140" rx="16" fill="#1e1f20"/>
  <text x="654" y="400" fill="#e3e3e3" font-family="Cantarell, sans-serif" font-size="14">Criar um manifesto</text>
  <text x="654" y="422" fill="#e3e3e3" font-family="Cantarell, sans-serif" font-size="14">Flatpak para Flathub</text>

  <rect x="852" y="365" width="200" height="140" rx="16" fill="#1e1f20"/>
  <text x="870" y="400" fill="#e3e3e3" font-family="Cantarell, sans-serif" font-size="14">Revisar script Python</text>
  <text x="870" y="422" fill="#e3e3e3" font-family="Cantarell, sans-serif" font-size="14">com PyGObject GTK 4</text>

  <!-- Barra de prompt inferior do Gemini -->
  <rect x="380" y="690" width="700" height="64" rx="32" fill="#1e1f20"/>
  <text x="415" y="727" fill="#8e918f" font-family="Cantarell, sans-serif" font-size="16">Peça ao Gemini…</text>
  <circle cx="1044" cy="722" r="20" fill="#282a2c"/>
  <path d="M1038 722 L1050 722 M1044 716 L1044 728" stroke="#e3e3e3" stroke-width="2"/>
</svg>
"""


def generate_screenshot() -> None:
    base_dir = Path(__file__).resolve().parent
    screenshots_dir = base_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    png_path = screenshots_dir / "main-dark.png"

    loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
    loader.set_size(1200, 820)
    loader.write(SCREENSHOT_SVG.strip().encode("utf-8"))
    loader.close()
    pixbuf = loader.get_pixbuf()
    if pixbuf is not None:
        pixbuf.savev(str(png_path), "png", [], [])
        print(f"✔ Screenshot gerado em: {png_path} ({pixbuf.get_width()}x{pixbuf.get_height()})")


if __name__ == "__main__":
    generate_screenshot()
