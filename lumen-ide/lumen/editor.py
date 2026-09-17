"""
editor.py
=========

Representa uma aba de edição de código, usando GtkSourceView5 para
realce de sintaxe, números de linha, indentação inteligente e
destaque da linha atual.
"""

from __future__ import annotations

import os
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk, GtkSource, GObject, Gio, GLib  # noqa: E402


class LumenEditor(Gtk.Box):
    """Uma página de editor: um único arquivo aberto."""

    __gtype_name__ = "LumenEditor"

    __gsignals__ = {
        "modified-changed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, file_path: Optional[str] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.file_path = file_path
        self._is_new = file_path is None

        self.buffer = GtkSource.Buffer()
        self._setup_language_and_style()

        self.view = GtkSource.View(buffer=self.buffer)
        self.view.set_show_line_numbers(True)
        self.view.set_highlight_current_line(True)
        self.view.set_auto_indent(True)
        self.view.set_indent_on_tab(True)
        self.view.set_tab_width(4)
        self.view.set_insert_spaces_instead_of_tabs(True)
        self.view.set_monospace(True)
        self.view.set_top_margin(10)
        self.view.set_bottom_margin(10)
        self.view.set_left_margin(8)
        self.view.add_css_class("lumen-editor")

        scroller = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroller.set_child(self.view)
        self.append(scroller)

        self.buffer.connect("changed", self._on_changed)
        self._modified = False

        if file_path and os.path.exists(file_path):
            self.load_from_disk(file_path)

    # ------------------------------------------------------------------ #
    # Carregamento / gravação
    # ------------------------------------------------------------------ #

    def _setup_language_and_style(self) -> None:
        lang_manager = GtkSource.LanguageManager.get_default()
        style_manager = GtkSource.StyleSchemeManager.get_default()

        if self.file_path:
            guessed = lang_manager.guess_language(self.file_path, None)
            if guessed:
                self.buffer.set_language(guessed)

        # Escolhe um esquema de cores agradável, com fallback seguro.
        scheme = style_manager.get_scheme("Adwaita") or style_manager.get_scheme("classic")
        if scheme:
            self.buffer.set_style_scheme(scheme)

    def load_from_disk(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError as exc:
            raise RuntimeError(f"Não foi possível abrir {path}: {exc}") from exc

        self.buffer.begin_not_undoable_action()
        self.buffer.set_text(content)
        self.buffer.end_not_undoable_action()
        self.file_path = path
        self._is_new = False
        self._modified = False
        self._setup_language_and_style()

    def save(self, path: Optional[str] = None) -> None:
        target = path or self.file_path
        if not target:
            raise RuntimeError("Nenhum caminho de destino definido para salvar.")

        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, True)

        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(text)

        self.file_path = target
        self._is_new = False
        self._modified = False
        self.emit("modified-changed", False)
        self._setup_language_and_style()

    # ------------------------------------------------------------------ #
    # Estado
    # ------------------------------------------------------------------ #

    @property
    def display_name(self) -> str:
        if self.file_path:
            return os.path.basename(self.file_path)
        return "Sem título"

    @property
    def is_modified(self) -> bool:
        return self._modified

    @property
    def is_new(self) -> bool:
        return self._is_new

    def get_text(self) -> str:
        start, end = self.buffer.get_bounds()
        return self.buffer.get_text(start, end, True)

    def _on_changed(self, _buffer) -> None:
        if not self._modified:
            self._modified = True
            self.emit("modified-changed", True)
