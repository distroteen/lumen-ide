"""
command_palette.py
===================

Paleta de comandos flutuante (Ctrl+Shift+P), inspirada no Spotlight
da Apple / paleta de comandos do VS Code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GObject, Gio  # noqa: E402


@dataclass
class Command:
    id: str
    title: str
    subtitle: str
    action: Callable[[], None]


class CommandEntry(GObject.Object):
    __gtype_name__ = "CommandEntry"

    def __init__(self, command: Command):
        super().__init__()
        self.command = command


class LumenCommandPalette(Adw.Dialog):
    __gtype_name__ = "LumenCommandPalette"

    def __init__(self, commands: list[Command]):
        super().__init__(content_width=560, content_height=420)
        self.add_css_class("lumen-command-palette")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                       margin_top=10, margin_bottom=10, margin_start=10, margin_end=10)

        self.search_entry = Gtk.SearchEntry(placeholder_text="Digite um comando…")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_activate_selected)
        box.append(self.search_entry)

        self._all_commands = commands
        self._store = Gio.ListStore(item_type=CommandEntry)
        for cmd in commands:
            self._store.append(CommandEntry(cmd))

        self.list_view = Gtk.ListView()
        selection = Gtk.SingleSelection(model=self._store)
        self.list_view.set_model(selection)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_setup)
        factory.connect("bind", self._on_bind)
        self.list_view.set_factory(factory)
        self.list_view.connect("activate", self._on_row_activated)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self.list_view)
        box.append(scroller)

        self.set_child(box)
        self.set_focus(self.search_entry)

    def _on_setup(self, _factory, list_item: Gtk.ListItem) -> None:
        row = Adw.ActionRow()
        list_item.set_child(row)

    def _on_bind(self, _factory, list_item: Gtk.ListItem) -> None:
        entry: CommandEntry = list_item.get_item()
        row: Adw.ActionRow = list_item.get_child()
        row.set_title(entry.command.title)
        row.set_subtitle(entry.command.subtitle)

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text().lower().strip()
        self._store.remove_all()
        for cmd in self._all_commands:
            if query in cmd.title.lower() or query in cmd.subtitle.lower():
                self._store.append(CommandEntry(cmd))

    def _on_row_activated(self, _view, position: int) -> None:
        entry: CommandEntry = self._store.get_item(position)
        self.close()
        entry.command.action()

    def _on_activate_selected(self, _entry) -> None:
        if self._store.get_n_items() > 0:
            entry: CommandEntry = self._store.get_item(0)
            self.close()
            entry.command.action()
