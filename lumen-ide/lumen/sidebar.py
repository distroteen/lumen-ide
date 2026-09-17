"""
sidebar.py
==========

Painel lateral com a árvore de arquivos do projeto aberto.
Usa Gtk.TreeListModel + Gtk.ListView (abordagem moderna do GTK4,
performática mesmo com diretórios grandes, pois carrega sob demanda).
"""

from __future__ import annotations

import os
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GObject, GLib  # noqa: E402


class FileNode(GObject.Object):
    __gtype_name__ = "FileNode"

    def __init__(self, path: str, is_dir: bool):
        super().__init__()
        self.path = path
        self.is_dir = is_dir

    @property
    def name(self) -> str:
        return os.path.basename(self.path) or self.path


class LumenSidebar(Gtk.Box):
    __gtype_name__ = "LumenSidebar"

    __gsignals__ = {
        "file-activated": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("lumen-sidebar")
        self.root_path: Optional[str] = None

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, margin_top=8,
                          margin_bottom=4, margin_start=10, margin_end=10)
        self.title_label = Gtk.Label(label="Sem projeto", xalign=0, hexpand=True)
        self.title_label.add_css_class("heading")
        header.append(self.title_label)

        open_btn = Gtk.Button(icon_name="folder-open-symbolic", tooltip_text="Abrir pasta de projeto")
        open_btn.add_css_class("flat")
        open_btn.connect("clicked", self._on_open_folder_clicked)
        header.append(open_btn)
        self.append(header)

        self.tree_view = Gtk.ListView()
        self.tree_view.add_css_class("navigation-sidebar")

        self._store = Gio.ListStore(item_type=FileNode)
        self.tree_model = Gtk.TreeListModel.new(
            self._store, False, False, self._create_children_model
        )
        selection = Gtk.SingleSelection(model=self.tree_model)
        self.tree_view.set_model(selection)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        self.tree_view.set_factory(factory)
        self.tree_view.connect("activate", self._on_row_activated)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self.tree_view)
        self.append(scroller)

    # ------------------------------------------------------------------ #

    def open_folder(self, folder_path: str) -> None:
        self.root_path = folder_path
        self.title_label.set_label(os.path.basename(folder_path.rstrip("/")) or folder_path)
        self._store.remove_all()
        for node in self._list_dir(folder_path):
            self._store.append(node)

    def _list_dir(self, path: str) -> list[FileNode]:
        try:
            entries = sorted(
                os.scandir(path),
                key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()),
            )
        except OSError:
            return []

        nodes = []
        for entry in entries:
            if entry.name.startswith(".git"):
                continue
            nodes.append(FileNode(entry.path, entry.is_dir(follow_symlinks=False)))
        return nodes

    def _create_children_model(self, item: FileNode):
        if not item.is_dir:
            return None
        children = self._list_dir(item.path)
        if not children:
            return None
        store = Gio.ListStore(item_type=FileNode)
        for child in children:
            store.append(child)
        return store

    # ------------------------------------------------------------------ #

    def _on_factory_setup(self, _factory, list_item: Gtk.ListItem) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        expander = Gtk.TreeExpander()
        icon = Gtk.Image()
        label = Gtk.Label(xalign=0)
        box.append(icon)
        box.append(label)
        expander.set_child(box)
        list_item.set_child(expander)
        list_item._icon = icon
        list_item._label = label
        list_item._expander = expander

    def _on_factory_bind(self, _factory, list_item: Gtk.ListItem) -> None:
        row = list_item.get_item()
        list_item._expander.set_list_row(row)
        node: FileNode = row.get_item()
        list_item._label.set_label(node.name)
        if node.is_dir:
            list_item._icon.set_from_icon_name("folder-symbolic")
        else:
            list_item._icon.set_from_icon_name(self._icon_for_file(node.name))

    @staticmethod
    def _icon_for_file(name: str) -> str:
        ext = os.path.splitext(name)[1].lower()
        mapping = {
            ".py": "text-x-python-symbolic",
            ".js": "text-x-javascript-symbolic",
            ".ts": "text-x-javascript-symbolic",
            ".rs": "text-x-generic-symbolic",
            ".c": "text-x-csrc-symbolic",
            ".cpp": "text-x-c++src-symbolic",
            ".md": "text-x-generic-symbolic",
            ".json": "text-x-generic-symbolic",
        }
        return mapping.get(ext, "text-x-generic-symbolic")

    def _on_row_activated(self, _view, position: int) -> None:
        selection = self.tree_view.get_model()
        row = selection.get_item(position)
        node: FileNode = row.get_item()
        if not node.is_dir:
            self.emit("file-activated", node.path)
        else:
            row.set_expanded(not row.get_expanded())

    def _on_open_folder_clicked(self, _button) -> None:
        dialog = Gtk.FileDialog(title="Abrir pasta de projeto")
        dialog.select_folder(self.get_root(), None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog: Gtk.FileDialog, result) -> None:
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if folder:
            self.open_folder(folder.get_path())
