"""
Permite executar o pacote diretamente com `python3 -m lumen`,
além de `python3 -m lumen.main`.
"""

from .main import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
