"""
terminal_panel.py
==================

Painel inferior que exibe a saída (stdout/stderr) da execução do
arquivo atual, com streaming em tempo real e opção de cancelar.
"""

from __future__ import annotations

import threading
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango  # noqa: E402

from .language_runner import LanguageRunner, RunResult


class LumenTerminalPanel(Gtk.Box):
    __gtype_name__ = "LumenTerminalPanel"

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("lumen-terminal")

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, margin_bottom=6)
        title = Gtk.Label(label="Saída", xalign=0, hexpand=True)
        title.add_css_class("heading")
        toolbar.append(title)

        self.status_badge = Gtk.Label(label="pronto")
        self.status_badge.add_css_class("lumen-lang-badge")
        toolbar.append(self.status_badge)

        self.cancel_btn = Gtk.Button(icon_name="process-stop-symbolic", tooltip_text="Cancelar execução")
        self.cancel_btn.add_css_class("flat")
        self.cancel_btn.set_sensitive(False)
        self.cancel_btn.connect("clicked", self._on_cancel_clicked)
        toolbar.append(self.cancel_btn)

        clear_btn = Gtk.Button(icon_name="edit-clear-symbolic", tooltip_text="Limpar saída")
        clear_btn.add_css_class("flat")
        clear_btn.connect("clicked", lambda *_: self.clear())
        toolbar.append(clear_btn)

        self.append(toolbar)

        self.text_view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.buffer = self.text_view.get_buffer()
        self._stderr_tag = self.buffer.create_tag("stderr", foreground="#ff6b6b")
        self._stdout_tag = self.buffer.create_tag("stdout")
        self._ok_tag = self.buffer.create_tag("ok", foreground="#34c759", weight=Pango.Weight.BOLD)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self.text_view)
        self.append(scroller)

        self._runner: Optional[LanguageRunner] = None

    def clear(self) -> None:
        self.buffer.set_text("")

    def run_file(self, file_path: str) -> None:
        self.clear()
        self.status_badge.set_label("executando…")
        self.cancel_btn.set_sensitive(True)

        self._runner = LanguageRunner()
        thread = threading.Thread(
            target=self._runner.run,
            args=(file_path, self._on_output, self._on_finished),
            daemon=True,
        )
        thread.start()

    def _on_cancel_clicked(self, _button) -> None:
        if self._runner:
            self._runner.cancel()

    # As duas funções abaixo são chamadas de uma thread de trabalho;
    # usam GLib.idle_add para atualizar a UI com segurança na thread principal.

    def _on_output(self, line: str, is_stderr: bool) -> None:
        GLib.idle_add(self._append_line, line, is_stderr)

    def _append_line(self, line: str, is_stderr: bool) -> bool:
        end = self.buffer.get_end_iter()
        tag = self._stderr_tag if is_stderr else self._stdout_tag
        self.buffer.insert_with_tags(end, line + "\n", tag)
        return False

    def _on_finished(self, result: RunResult) -> None:
        GLib.idle_add(self._finish_ui, result)

    def _finish_ui(self, result: RunResult) -> bool:
        self.cancel_btn.set_sensitive(False)
        if result.cancelled:
            self.status_badge.set_label("cancelado")
        elif result.returncode == 0:
            self.status_badge.set_label("concluído ✓")
        else:
            self.status_badge.set_label(f"erro (código {result.returncode})")
        return False
