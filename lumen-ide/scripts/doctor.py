#!/usr/bin/env python3
"""
doctor.py — diagnostica o ambiente antes de rodar o Lumen IDE.

Verifica se GTK4, libadwaita, GtkSourceView5 e PyGObject estão
disponíveis, e lista quais linguagens de programação o sistema já
consegue executar, sem precisar abrir a interface gráfica.

Uso:
    python3 scripts/doctor.py
"""

from __future__ import annotations

import importlib
import shutil
import sys


def check_python_module(module: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module)
        return True, "ok"
    except ImportError as exc:
        return False, str(exc)


def main() -> int:
    print("Lumen IDE — diagnóstico do ambiente\n" + "=" * 40)

    print(f"Python: {sys.version.split()[0]}")
    ok = sys.version_info >= (3, 11)
    print(f"  {'✓' if ok else '✗'} Requer Python >= 3.11")

    gi_ok, gi_msg = check_python_module("gi")
    print(f"{'✓' if gi_ok else '✗'} PyGObject (gi): {'ok' if gi_ok else gi_msg}")

    if gi_ok:
        import gi

        for name, version in (("Gtk", "4.0"), ("Adw", "1"), ("GtkSource", "5")):
            try:
                gi.require_version(name, version)
                importlib.import_module(f"gi.repository.{name}")
                print(f"✓ {name} {version} disponível")
            except (ValueError, ImportError) as exc:
                print(f"✗ {name} {version} indisponível: {exc}")

    print("\nLinguagens de programação detectadas:\n" + "-" * 40)
    try:
        sys.path.insert(0, ".")
        from lumen import language_runner

        for lang in language_runner.LANGUAGES:
            available = language_runner.is_available(lang)
            marker = "✓" if available else "✗"
            extra = "" if available else f" (faltando: {', '.join(language_runner.missing_binaries(lang))})"
            print(f"{marker} {lang.display_name}{extra}")
    except ImportError:
        # Fallback simples caso o pacote lumen ainda não esteja instalado.
        candidates = ["python3", "node", "gcc", "g++", "rustc", "go", "javac", "ruby", "php", "lua", "perl"]
        for binary in candidates:
            marker = "✓" if shutil.which(binary) else "✗"
            print(f"{marker} {binary}")

    print("\nSe algo estiver faltando, rode ./scripts/install.sh ou consulte o README.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
