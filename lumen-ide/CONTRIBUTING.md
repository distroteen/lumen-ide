# Contribuindo com o Lumen IDE

Obrigado pelo interesse em contribuir! 🎉

## Ambiente de desenvolvimento

```bash
# Dependências de sistema (exemplo Fedora)
sudo dnf install python3 python3-gobject gtk4 libadwaita gtksourceview5

# Clonar e instalar em modo editável
git clone https://github.com/<seu-usuario>/lumen-ide.git
cd lumen-ide

# Em distros com Python "externally managed" (PEP 668 — Arch, Fedora
# recentes, Debian 12+), use uma venv com acesso aos pacotes de
# sistema (necessário para enxergar o módulo `gi`/GTK4):
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e .

# Rodar a partir do código-fonte (com a venv ativada, ou diretamente
# com python3 do sistema se as dependências já estiverem instaladas)
python3 -m lumen.main
# ou, de forma equivalente:
python3 -m lumen
```

## Diretrizes de design

O Lumen segue uma linguagem visual inspirada nas diretrizes de Human
Interface da Apple, adaptada ao GTK4/libadwaita — veja `lumen/style.css`
antes de propor mudanças visuais. Priorize: clareza, hierarquia
tipográfica, espaçamento generoso e transições suaves (150–200ms).

## Adicionando suporte a uma nova linguagem

Edite `lumen/language_runner.py` e adicione uma nova `LanguageSpec` à
lista `LANGUAGES`, definindo extensões, binários necessários e o
comando de execução/compilação.

## Pull requests

1. Abra uma issue descrevendo a mudança antes de PRs grandes.
2. Mantenha commits pequenos e descritivos.
3. Rode `ruff check lumen/` antes de enviar.
