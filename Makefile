APP_ID := com.google_unofficial.Gemini
MANIFEST := $(APP_ID).yaml
METAINFO := $(APP_ID).metainfo.xml
DESKTOP := $(APP_ID).desktop
BUILD_DIR := build-dir
REPO_DIR := repo

.PHONY: all icons lint build run clean

all: icons lint build

icons:
	@echo "==> Gerando ícones (SVG e PNG 128x128)..."
	python3 generate_icon.py

lint:
	@echo "==> Validando arquivo .desktop..."
	@if command -v desktop-file-validate >/dev/null 2>&1; then \
		desktop-file-validate $(DESKTOP); \
	fi
	@echo "==> Validando AppStream metainfo..."
	@if command -v flatpak-builder-lint >/dev/null 2>&1; then \
		flatpak-builder-lint appstream $(METAINFO); \
		flatpak-builder-lint manifest $(MANIFEST); \
	elif flatpak info org.flatpak.Builder >/dev/null 2>&1; then \
		flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream $(METAINFO); \
		flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest $(MANIFEST); \
	else \
		echo "Aviso: flatpak-builder-lint não encontrado localmente; executando appstreamcli validate..."; \
		appstreamcli validate --no-net $(METAINFO); \
	fi

build: icons
	@echo "==> Compilando e instalando pacote Flatpak localmente..."
	flatpak-builder --user --install --force-clean $(BUILD_DIR) $(MANIFEST)

run:
	@echo "==> Executando $(APP_ID)..."
	flatpak run $(APP_ID)

clean:
	rm -rf $(BUILD_DIR) $(REPO_DIR) .flatpak-builder
