"""
main.py
=======

Ponto de entrada do Lumen IDE.
"""

from __future__ import annotations

import sys


def main() -> int:
    from .application import LumenApplication

    app = LumenApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
