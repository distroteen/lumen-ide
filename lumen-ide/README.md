# Lumen IDE

**Um interpretador · IDE · compilador multi-linguagem para Linux, com uma interface extremamente moderna inspirada no design da Apple.**

Lumen IDE é um editor de código nativo, leve e bonito, construído com **GTK4 + libadwaita**, feito para rodar perfeitamente em **GNOME** e **Hyprland**, com suporte oficial para as três grandes famílias de distribuições Linux: **Debian/Ubuntu**, **Fedora/RHEL** e **Arch**.

Tudo roda 100% localmente na máquina do usuário — nenhum código é enviado para servidores externos. Não há telemetria, não há contas, não há nuvem.

---

## ✨ Destaques

- **Design "Apple-grade"** — cantos arredondados, tipografia refinada (Inter/SF-like), paleta adaptativa clara/escura, header bar com decorações client-side (CSD), animações suaves e um modo opcional de "botões de tráfego" no estilo macOS.
- **Multi-linguagem de verdade** — detecta automaticamente o interpretador/compilador instalado no sistema para: Python, JavaScript/Node, TypeScript, C, C++, Rust, Go, Java, C#, Ruby, PHP, Lua, Perl, Bash e Kotlin.
- **Zero configuração** — o Lumen detecta as toolchains disponíveis no seu sistema e mostra exatamente o que falta instalar, sem travar o app.
- **Terminal de saída integrado** — execução assíncrona com streaming de stdout/stderr em tempo real, sem congelar a interface.
- **Explorador de projetos** com árvore de arquivos, criação/renomeação/exclusão, e abertura de pastas inteiras.
- **Abas múltiplas** com indicador de alterações não salvas, atalhos completos de teclado e paleta de comandos (`Ctrl+Shift+P`).
- **Realce de sintaxe** via GtkSourceView5, com todos os esquemas de cores do sistema (Adwaita light/dark, Kate, etc.).
- **Seguro por padrão** — nenhuma execução remota, nenhuma escrita fora do diretório do projeto sem confirmação, instaladores assinados/verificáveis (checksums SHA256) e sandboxing opcional via Flatpak.
- **Feito para GNOME e Hyprland** — respeita `prefers-color-scheme`, funciona bem com `xdg-desktop-portal`, e inclui dicas de `windowrulev2` para quem usa Hyprland.

---

## 📦 Instalação

### Instalador universal (recomendado)

```bash
curl -fsSL https://raw.githubusercontent.com/distroteen/lumen-ide/main/scripts/install.sh | bash
```

O script detecta automaticamente sua distribuição (`/etc/os-release`) e usa o gerenciador de pacotes correto (`apt`, `dnf` ou `pacman`) para instalar as dependências de sistema (GTK4, libadwaita, GtkSourceView5, Python 3.11+) e em seguida instala o Lumen IDE em `~/.local`.

> Sempre revise scripts antes de rodar com `curl | bash`. O conteúdo completo está em [`scripts/install.sh`](scripts/install.sh).

### Debian / Ubuntu (.deb)

```bash
sudo apt install ./lumen-ide_1.0.0_amd64.deb
```

Pacote gerado a partir de [`packaging/debian`](packaging/debian).

### Fedora / RHEL (.rpm)

```bash
sudo dnf install ./lumen-ide-1.0.0.x86_64.rpm
```

Especificação em [`packaging/rpm/lumen-ide.spec`](packaging/rpm/lumen-ide.spec).

### Arch / Manjaro (AUR / PKGBUILD)

```bash
git clone https://github.com/distroteen/lumen-ide.git
cd lumen-ide/lumen-ide/packaging/arch
makepkg -si
```

### Flatpak (sandboxed)

```bash
flatpak install packaging/flatpak/com.lumen.ide.yml
```

---

## 🖥️ Requisitos

- Linux com servidor gráfico Wayland ou X11 (GNOME, Hyprland, KDE, etc.)
- GTK 4.12+
- libadwaita 1.4+
- GtkSourceView 5
- Python 3.11+ com PyGObject
- Compiladores/interpretadores das linguagens que você quiser usar (o Lumen detecta o que já está instalado)

---

## 🚀 Uso rápido

| Atalho | Ação |
|---|---|
| `Ctrl+N` | Novo arquivo |
| `Ctrl+O` | Abrir arquivo |
| `Ctrl+Shift+O` | Abrir pasta de projeto |
| `Ctrl+S` | Salvar |
| `Ctrl+Shift+S` | Salvar como |
| `Ctrl+R` / `F5` | Executar arquivo atual |
| `Ctrl+Shift+P` | Paleta de comandos |
| `Ctrl+,` | Preferências |
| `Ctrl+W` | Fechar aba |
| `Ctrl+Q` | Sair |

---

## 🧩 Linguagens suportadas nativamente

| Linguagem | Comando de execução detectado |
|---|---|
| Python | `python3 arquivo.py` |
| JavaScript | `node arquivo.js` |
| TypeScript | `tsx arquivo.ts` / `ts-node` |
| C | `gcc arquivo.c -o /tmp/lumen_out && /tmp/lumen_out` |
| C++ | `g++ arquivo.cpp -o /tmp/lumen_out && /tmp/lumen_out` |
| Rust | `rustc arquivo.rs -o /tmp/lumen_out && /tmp/lumen_out` |
| Go | `go run arquivo.go` |
| Java | `javac + java` |
| C# | `dotnet run` |
| Ruby | `ruby arquivo.rb` |
| PHP | `php arquivo.php` |
| Lua | `lua arquivo.lua` |
| Perl | `perl arquivo.pl` |
| Bash | `bash arquivo.sh` |
| Kotlin | `kotlinc -script arquivo.kts` |

Cada execução roda em um processo isolado, com timeout configurável e sem privilégios elevados.

---

## 🏗️ Arquitetura do projeto

```
lumen-ide/
├── lumen/                  # Código-fonte da aplicação (Python + GTK4/libadwaita)
│   ├── main.py              # Ponto de entrada
│   ├── application.py       # Adw.Application
│   ├── window.py            # Janela principal
│   ├── editor.py            # Aba de edição (GtkSourceView)
│   ├── sidebar.py           # Árvore de arquivos do projeto
│   ├── terminal_panel.py    # Painel de saída/execução
│   ├── language_runner.py   # Detecção e execução de linguagens
│   ├── command_palette.py   # Paleta de comandos estilo Spotlight
│   ├── preferences.py       # Janela de preferências
│   └── style.css            # Tema visual customizado
├── data/                    # Ícone, .desktop, metainfo AppStream
├── packaging/                # Empacotamento nativo (deb, rpm, Arch, Flatpak)
├── scripts/install.sh        # Instalador universal multi-distro
└── .github/workflows/        # CI para build automático dos pacotes
```

---

## 🛠️ Solução de problemas

**`error: externally-managed-environment` ao instalar**
Distros recentes (Arch, Fedora, Debian 12+) protegem o Python do
sistema por padrão (PEP 668). O `install.sh` já resolve isso sozinho
usando `pipx` — se você estiver instalando manualmente, use `pipx
install --system-site-packages .` (o `--system-site-packages` é
necessário para o PyGObject do sistema ser enxergado dentro do venv
isolado do pipx) em vez de `pip install --user`.

**`makepkg` reclama que `lumen-ide-1.0.0.tar.gz não foi encontrado`**
O `PKGBUILD` builda direto do checkout git já clonado — não baixe um
tarball separado. Certifique-se de rodar `makepkg -si` de dentro de
`packaging/arch/` **após** ter clonado o repositório inteiro (não
apenas a pasta `packaging/`).

**Rodar a partir do código-fonte sem instalar**
```bash
cd lumen-ide
python3 -m lumen.main
# ou
python3 -m lumen
```
(`python3 -m lumen.main`/`-m lumen` a partir da raiz do repositório;
executar `python3 -m lumen/main.py` ou de dentro da pasta `lumen/`
não funciona — o Python precisa resolver o caminho como pacote, não
como arquivo solto.)

**`./scripts/doctor.py` mostra tudo verde mas o app não abre pelo menu**
Rode `update-desktop-database ~/.local/share/applications` e
`gtk-update-icon-cache -f ~/.local/share/icons/hicolor` manualmente, ou
abra um novo terminal — alguns shells cacheiam a lista de aplicativos.

---

## 🔒 Segurança

- Nenhuma conexão de rede é feita pelo aplicativo em si (100% offline por padrão).
- O instalador verifica checksums SHA256 dos artefatos antes de instalar.
- Execução de código roda em subprocessos isolados, nunca com `sudo`.
- Os pacotes `.deb`/`.rpm`/`PKGBUILD` não requerem scripts pós-instalação com privilégios além dos necessários para copiar arquivos e registrar o `.desktop`.
- Build reprodutível via GitHub Actions, para que qualquer pessoa possa auditar o pipeline.

---

## 🖌️ Filosofia de design

O Lumen segue princípios de clareza visual, profundidade sutil e hierarquia tipográfica muito próximos das diretrizes de Human Interface da Apple — adaptados ao ecossistema GTK/libadwaita:

- Bordas arredondadas de 12–14px em painéis e cartões
- Sombras suaves e translúcidas para dar profundidade sem exagero
- Paleta de acentos vibrante mas comedida, com contraste AA garantido
- Tipografia com boa respiração (line-height generoso, pesos variados)
- Transições de 150–200ms em hovers e trocas de estado
- Suporte nativo a modo claro/escuro seguindo o tema do sistema

---

## 📄 Licença

MIT — veja [LICENSE](LICENSE).

## 🤝 Contribuindo

Pull requests são bem-vindos. Abra uma issue antes de mudanças grandes para alinharmos o design.
