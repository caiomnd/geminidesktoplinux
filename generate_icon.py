#!/usr/bin/env python3
"""
Gerenciador e sincronizador do ícone oficial do Google Gemini para com.google_unofficial.Gemini.
- Mantém o SVG oficial do Google Gemini (com o path vetorial exato da estrela de 4 pontas e gradiente oficial).
- Consulta dinamicamente https://gemini.google.com para detectar e baixar automaticamente
  novos ícones oficiais (SVG/PNG de alta resolução em gstatic.com) caso a Google atualize a marca.
- Atualiza os diretórios do projeto e o cache de ícones do GNOME (~/.local/share/icons/hicolor).
"""

import hashlib
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

APP_ID = "com.google_unofficial.Gemini"
GEMINI_URL = "https://gemini.google.com/"

# SVG Oficial do Google Gemini (baseado no path vetorial 24x24 oficial do Google Gemini escalado para 128x128)
OFFICIAL_GEMINI_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <defs>
    <radialGradient id="geminiOfficialGrad" cx="22%" cy="82%" r="92%" fx="18%" fy="85%">
      <stop offset="0%" stop-color="#1b72e8"/>
      <stop offset="35%" stop-color="#4e82ee"/>
      <stop offset="68%" stop-color="#9b72cb"/>
      <stop offset="100%" stop-color="#d96570"/>
    </radialGradient>
  </defs>
  <g transform="translate(8, 8) scale(4.6666667)">
    <path fill="url(#geminiOfficialGrad)"
          d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.93a12.3 12.3 0 0 1 3.81 2.58q2.19 1.62 2.55 3.81z"/>
  </g>
</svg>
"""


def render_bytes_to_png(data: bytes, png_path: Path, size: int = 128) -> bool:
    """Converte bytes de imagem (SVG ou PNG) em um PNG redimensionado de 128x128."""
    try:
        loader = GdkPixbuf.PixbufLoader()
        loader.set_size(size, size)
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        if pixbuf is None:
            return False
        if pixbuf.get_width() != size or pixbuf.get_height() != size:
            pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
        pixbuf.savev(str(png_path), "png", [], [])
        return True
    except Exception:
        return False


def fetch_latest_official_icon_from_google(timeout: float = 6.0) -> tuple[bytes | None, str | None]:
    """
    Busca em https://gemini.google.com os assets oficiais mais recentes de ícone (`gstatic.com/lamda/images/...`).
    Retorna (bytes_do_icone, extensao) ou (None, None) se estiver offline.
    """
    req = urllib.request.Request(
        GEMINI_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None, None

    # 1. Procura por tags <link rel="icon" | "apple-touch-icon"> ou URLs de sparkle no gstatic
    candidates: list[str] = []

    # Busca URLs de alta resolução ou vetoriais do Gemini no gstatic
    svg_matches = re.findall(
        r"https://www\.gstatic\.com/lamda/images/[a-zA-Z0-9_.-]*gemini_sparkle[a-zA-Z0-9_.-]*\.svg",
        html,
    )
    png_512_matches = re.findall(
        r"https://www\.gstatic\.com/lamda/images/[a-zA-Z0-9_.-]*512[a-zA-Z0-9_.-]*\.png",
        html,
    )
    png_matches = re.findall(
        r"https://www\.gstatic\.com/lamda/images/[a-zA-Z0-9_.-]*(?:sparkle|favicon|gemini)[a-zA-Z0-9_.-]*\.png",
        html,
    )

    candidates.extend(svg_matches)
    candidates.extend(png_512_matches)
    candidates.extend(png_matches)

    # Também verifica <link rel="icon" href="...">
    for match in re.finditer(r'<link[^>]+rel=["\'](?:apple-touch-icon|icon|shortcut icon)["\'][^>]*>', html, re.I):
        tag = match.group(0)
        href_m = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
        if href_m:
            href = href_m.group(1)
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = "https://gemini.google.com" + href
            if href.startswith("http"):
                candidates.append(href)

    for url in candidates:
        try:
            icon_req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(icon_req, timeout=timeout) as icon_resp:
                data = icon_resp.read()
                if len(data) > 100:
                    ext = "svg" if url.lower().endswith(".svg") or b"<svg" in data[:300] else "png"
                    return data, ext
        except Exception:
            continue

    return None, None


def sync_to_local_desktop(png_path: Path, svg_path: Path) -> None:
    """Sincroniza os ícones atualizados com ~/.local/share/icons/hicolor para o GNOME Shell."""
    try:
        local_icons = Path.home() / ".local" / "share" / "icons" / "hicolor"
        local_128 = local_icons / "128x128" / "apps"
        local_scalable = local_icons / "scalable" / "apps"
        local_128.mkdir(parents=True, exist_ok=True)
        local_scalable.mkdir(parents=True, exist_ok=True)

        shutil.copy2(png_path, local_128 / f"{APP_ID}.png")
        shutil.copy2(svg_path, local_scalable / f"{APP_ID}.svg")

        if shutil.which("gtk-update-icon-cache"):
            subprocess.run(
                ["gtk-update-icon-cache", "-f", "-t", str(local_icons)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    except Exception:
        pass


def generate_icons(check_remote: bool = True) -> bool:
    """
    Gera os ícones oficiais locais e, se check_remote=True, verifica nos servidores
    da Google se há uma versão mais nova do ícone do Gemini para atualizar automaticamente.
    Retorna True se houve atualização ou criação de arquivos.
    """
    base_dir = Path(__file__).resolve().parent
    icon_dir_128 = base_dir / "icons" / "128x128"
    icon_dir_scalable = base_dir / "icons" / "scalable"

    icon_dir_128.mkdir(parents=True, exist_ok=True)
    icon_dir_scalable.mkdir(parents=True, exist_ok=True)

    svg_path_128 = icon_dir_128 / f"{APP_ID}.svg"
    svg_path_scalable = icon_dir_scalable / f"{APP_ID}.svg"
    png_path = icon_dir_128 / f"{APP_ID}.png"

    default_svg_bytes = OFFICIAL_GEMINI_SVG.strip().encode("utf-8")

    updated = False
    if check_remote:
        remote_data, ext = fetch_latest_official_icon_from_google()
        if remote_data:
            if ext == "svg":
                old_hash = hashlib.sha256(svg_path_scalable.read_bytes()).hexdigest() if svg_path_scalable.exists() else ""
                new_hash = hashlib.sha256(remote_data).hexdigest()
                if old_hash != new_hash or not png_path.exists():
                    if render_bytes_to_png(remote_data, png_path, 128):
                        svg_path_128.write_bytes(remote_data)
                        svg_path_scalable.write_bytes(remote_data)
                        updated = True
                        print("✔ Ícone vetorial oficial do Google Gemini sincronizado via servidores da Google.")
            elif ext == "png":
                old_hash = hashlib.sha256(png_path.read_bytes()).hexdigest() if png_path.exists() else ""
                if render_bytes_to_png(remote_data, png_path, 128):
                    new_hash = hashlib.sha256(png_path.read_bytes()).hexdigest()
                    if not svg_path_scalable.exists():
                        svg_path_128.write_bytes(default_svg_bytes)
                        svg_path_scalable.write_bytes(default_svg_bytes)
                    if old_hash != new_hash:
                        updated = True
                        print("✔ Ícone PNG oficial do Google Gemini atualizado via servidores da Google.")

    # Garante que o SVG oficial e o PNG 128x128 existam sempre (mesmo offline)
    if not svg_path_scalable.exists() or not png_path.exists():
        svg_path_128.write_bytes(default_svg_bytes)
        svg_path_scalable.write_bytes(default_svg_bytes)
        render_bytes_to_png(default_svg_bytes, png_path, 128)
        updated = True
        print("✔ Ícone oficial padrão do Google Gemini gerado localmente (128x128 PNG e SVG).")

    if updated:
        sync_to_local_desktop(png_path, svg_path_scalable)

    return updated


if __name__ == "__main__":
    # Força regeneração com o ícone oficial do Google Gemini e tenta sincronizar com a Google
    base = Path(__file__).resolve().parent
    default_bytes = OFFICIAL_GEMINI_SVG.strip().encode("utf-8")
    (base / "icons" / "128x128").mkdir(parents=True, exist_ok=True)
    (base / "icons" / "scalable").mkdir(parents=True, exist_ok=True)
    (base / "icons" / "128x128" / f"{APP_ID}.svg").write_bytes(default_bytes)
    (base / "icons" / "scalable" / f"{APP_ID}.svg").write_bytes(default_bytes)
    render_bytes_to_png(default_bytes, base / "icons" / "128x128" / f"{APP_ID}.png", 128)
    generate_icons(check_remote=True)
    sync_to_local_desktop(
        base / "icons" / "128x128" / f"{APP_ID}.png",
        base / "icons" / "scalable" / f"{APP_ID}.svg",
    )
    print("✔ Ícones oficiais do Google Gemini prontos.")
