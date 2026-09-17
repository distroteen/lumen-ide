#!/usr/bin/env bash
#
# install.sh — instalador universal do Lumen IDE
#
# Funciona de duas formas:
#   1) Rodado de dentro do repositório já clonado:
#        ./scripts/install.sh
#   2) Rodado via pipe, sem repositório local:
#        curl -fsSL <url>/scripts/install.sh | bash
#      Nesse caso, o script clona o repositório para um diretório
#      temporário automaticamente.
#
# Detecta a distribuição Linux (via /etc/os-release), instala as
# dependências de sistema com o gerenciador de pacotes nativo
# (apt, dnf ou pacman) e instala o Lumen IDE para o usuário atual,
# sem tocar em nada fora do necessário e sem baixar binários de
# terceiros — apenas os repositórios oficiais da distro e o próprio
# código-fonte deste repositório.

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
RESET="\033[0m"

log()  { echo -e "${BLUE}==>${RESET} ${BOLD}$1${RESET}"; }
ok()   { echo -e "${GREEN}✓${RESET} $1"; }
warn() { echo -e "${YELLOW}!${RESET} $1"; }
fail() { echo -e "${RED}✗ $1${RESET}"; exit 1; }

if [[ "${EUID}" -eq 0 ]]; then
  fail "Não execute este script como root. Ele pedirá 'sudo' apenas quando necessário."
fi

if [[ ! -f /etc/os-release ]]; then
  fail "Não foi possível detectar sua distribuição (/etc/os-release ausente)."
fi

# shellcheck disable=SC1091
source /etc/os-release
DISTRO_ID="${ID:-desconhecido}"
DISTRO_LIKE="${ID_LIKE:-}"

log "Distribuição detectada: ${PRETTY_NAME:-$DISTRO_ID}"

# ------------------------------------------------------------------ #
# Localiza (ou clona) a raiz do repositório
# ------------------------------------------------------------------ #
#
# BASH_SOURCE[0] não existe quando o script é executado via
# `curl | bash` (o processo bash recebe o script pelo stdin, não por
# um arquivo). Por isso nunca acessamos BASH_SOURCE sem checar antes.

REPO_URL="https://github.com/distroteen/lumen-ide.git"
REPO_ROOT=""

if [[ -n "${BASH_SOURCE[0]:-}" ]] && [[ -f "${BASH_SOURCE[0]}" ]]; then
  CANDIDATE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  if [[ -f "$CANDIDATE_ROOT/pyproject.toml" ]]; then
    REPO_ROOT="$CANDIDATE_ROOT"
  fi
fi

if [[ -z "$REPO_ROOT" ]]; then
  log "Executando sem repositório local (modo 'curl | bash') — clonando…"
  command -v git >/dev/null 2>&1 || fail "git não encontrado; instale-o e rode este script novamente."
  TMP_CLONE_DIR="$(mktemp -d)"
  git clone --depth 1 "$REPO_URL" "$TMP_CLONE_DIR/lumen-ide"
  REPO_ROOT="$TMP_CLONE_DIR/lumen-ide"
fi

ok "Usando repositório em: $REPO_ROOT"

# ------------------------------------------------------------------ #
# Dependências de sistema
# ------------------------------------------------------------------ #

install_debian() {
  log "Instalando dependências via apt…"
  sudo apt update
  sudo apt install -y \
    python3 python3-pip python3-venv python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtksource-5 \
    libglib2.0-bin pipx
  ok "Dependências instaladas (apt)."
}

install_fedora() {
  log "Instalando dependências via dnf…"
  sudo dnf install -y \
    python3 python3-pip python3-gobject \
    gtk4 libadwaita gtksourceview5 glib2 pipx
  ok "Dependências instaladas (dnf)."
}

install_arch() {
  log "Instalando dependências via pacman…"
  sudo pacman -Sy --needed --noconfirm \
    python python-pip python-gobject python-pipx \
    gtk4 libadwaita gtksourceview5 glib2
  ok "Dependências instaladas (pacman)."
}

case "$DISTRO_ID" in
  ubuntu|debian|linuxmint|pop|elementary|zorin)
    install_debian
    ;;
  fedora|rhel|centos|rocky|almalinux)
    install_fedora
    ;;
  arch|manjaro|endeavouros|garuda|cachyos)
    install_arch
    ;;
  *)
    case "$DISTRO_LIKE" in
      *debian*) install_debian ;;
      *fedora*|*rhel*) install_fedora ;;
      *arch*) install_arch ;;
      *)
        fail "Distribuição '$DISTRO_ID' não suportada automaticamente. Instale manualmente: python3, PyGObject, GTK4, libadwaita e GtkSourceView5, depois use pipx ou uma venv para instalar o pacote na raiz do repositório."
        ;;
    esac
    ;;
esac

# ------------------------------------------------------------------ #
# Instalação do próprio Lumen IDE
# ------------------------------------------------------------------ #
#
# Distros modernas (Arch, Fedora recentes, Debian 12+) marcam o Python
# do sistema como "externally managed" (PEP 668) e recusam
# `pip install --user` puro. A forma correta e recomendada é usar
# pipx, que cria um ambiente isolado automaticamente. Se pipx não
# estiver disponível por algum motivo, caímos para
# `pip install --user --break-system-packages` como último recurso.

log "Instalando o Lumen IDE…"

if command -v pipx >/dev/null 2>&1; then
  # --system-site-packages é essencial aqui: o PyGObject (gi) que dá
  # acesso ao GTK4/libadwaita/GtkSourceView5 é instalado via pacote de
  # sistema (apt/dnf/pacman), não via PyPI. Sem essa flag, o venv do
  # pipx não enxergaria o módulo `gi` e o app falharia ao iniciar.
  pipx install --system-site-packages --force "$REPO_ROOT"
  ok "Instalado via pipx."
else
  warn "pipx não encontrado; tentando pip com --break-system-packages…"
  python3 -m pip install --user --break-system-packages --upgrade "$REPO_ROOT"
  ok "Instalado via pip (--user --break-system-packages)."
fi

# ------------------------------------------------------------------ #
# Ícone, atalho de aplicativo e schema do GSettings
# ------------------------------------------------------------------ #

log "Registrando ícone, atalho de aplicativo e schema do GSettings…"
mkdir -p "$HOME/.local/share/applications" \
         "$HOME/.local/share/icons/hicolor/scalable/apps" \
         "$HOME/.local/share/metainfo" \
         "$HOME/.local/share/glib-2.0/schemas"

install -Dm644 "$REPO_ROOT/data/com.lumen.ide.desktop" "$HOME/.local/share/applications/com.lumen.ide.desktop"
install -Dm644 "$REPO_ROOT/data/com.lumen.ide.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/com.lumen.ide.svg"
install -Dm644 "$REPO_ROOT/data/com.lumen.ide.appdata.xml" "$HOME/.local/share/metainfo/com.lumen.ide.appdata.xml"
install -Dm644 "$REPO_ROOT/lumen/resources/com.lumen.ide.gschema.xml" "$HOME/.local/share/glib-2.0/schemas/com.lumen.ide.gschema.xml"

if command -v glib-compile-schemas >/dev/null 2>&1; then
  glib-compile-schemas "$HOME/.local/share/glib-2.0/schemas" || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q "$HOME/.local/share/applications" || true
fi

ok "Lumen IDE instalado com sucesso!"
echo
if command -v pipx >/dev/null 2>&1; then
  echo -e "  Rode com:      ${BOLD}lumen-ide${RESET}  (pipx já cuida do PATH; se não funcionar, rode 'pipx ensurepath' e abra um novo terminal)"
else
  echo -e "  Rode com:      ${BOLD}lumen-ide${RESET}  (garanta que ~/.local/bin está no seu PATH)"
fi
echo -e "  Ou pelo menu:  procure por ${BOLD}Lumen IDE${RESET} no seu lançador de aplicativos"
echo
echo "Dica para usuários de Hyprland: adicione ao seu hyprland.conf, se preferir uma"
echo "janela flutuante centralizada:"
echo '  windowrulev2 = float, class:^(com.lumen.ide)$'
echo '  windowrulev2 = center, class:^(com.lumen.ide)$'
