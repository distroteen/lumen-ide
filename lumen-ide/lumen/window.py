"""
window.py
=========

Janela principal do Lumen IDE: header bar, sidebar, área de abas
de edição e painel de terminal, unidos em um Adw.ToolbarView com
um Gtk.Paned/Adw.OverlaySplitView responsivo.
"""

from __future__ import annotations

import os
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib  # noqa: E402

from .editor import LumenEditor
from .sidebar import LumenSidebar
from .terminal_panel import LumenTerminalPanel
from .command_palette import LumenCommandPalette, Command
from .preferences import LumenPreferencesWindow
from . import language_runner


class LumenWindow(Adw.ApplicationWindow):
    __gtype_name__ = "LumenWindow"

    def __init__(self, settings: Gio.Settings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings
        self.set_default_size(1280, 800)
        self.set_title("Lumen IDE")

        self._build_ui()
        self._setup_actions()
        self._apply_traffic_lights_preference()

        if self.settings:
            self.settings.connect("changed::traffic-lights", lambda *_: self._apply_traffic_lights_preference())

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        toolbar_view = Adw.ToolbarView()

        self.header = Adw.HeaderBar()
        self.header.add_css_class("lumen-headerbar")
        self._build_header_content()
        toolbar_view.add_top_bar(self.header)

        self.split_view = Adw.OverlaySplitView(sidebar_width_fraction=0.22, min_sidebar_width=200)

        self.sidebar = LumenSidebar()
        self.sidebar.connect("file-activated", self._on_file_activated)
        self.split_view.set_sidebar(self.sidebar)

        main_pane = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, vexpand=True)

        self.tab_view = Adw.TabView()
        self.tab_view.connect("close-page", self._on_tab_close)
        tab_bar = Adw.TabBar(view=self.tab_view, autohide=False)

        editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        editor_box.append(tab_bar)
        editor_box.append(self.tab_view)
        main_pane.set_start_child(editor_box)
        main_pane.set_resize_start_child(True)

        self.terminal_panel = LumenTerminalPanel()
        self.terminal_panel.set_size_request(-1, 220)
        main_pane.set_end_child(self.terminal_panel)
        main_pane.set_resize_end_child(False)
        main_pane.set_position(560)

        self.split_view.set_content(main_pane)
        toolbar_view.set_content(self.split_view)

        self.set_content(toolbar_view)

        self.new_tab()

    def _build_header_content(self) -> None:
        # Botões de tráfego estilo macOS (ocultos por padrão; ativáveis nas preferências)
        self.traffic_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        for name, css_class in (("close", "close"), ("minimize", "minimize"), ("maximize", "maximize")):
            btn = Gtk.Button()
            btn.add_css_class("lumen-traffic-light")
            btn.add_css_class(css_class)
            btn.connect("clicked", self._make_traffic_handler(name))
            self.traffic_box.append(btn)
        self.header.pack_start(self.traffic_box)
        self.traffic_box.set_visible(False)

        new_btn = Gtk.Button(icon_name="document-new-symbolic", tooltip_text="Novo arquivo (Ctrl+N)")
        new_btn.connect("clicked", lambda *_: self.new_tab())
        self.header.pack_start(new_btn)

        open_btn = Gtk.Button(icon_name="document-open-symbolic", tooltip_text="Abrir arquivo (Ctrl+O)")
        open_btn.connect("clicked", lambda *_: self.open_file_dialog())
        self.header.pack_start(open_btn)

        save_btn = Gtk.Button(icon_name="document-save-symbolic", tooltip_text="Salvar (Ctrl+S)")
        save_btn.connect("clicked", lambda *_: self.save_current())
        self.header.pack_start(save_btn)

        run_btn = Gtk.Button(label="Executar")
        run_btn.add_css_class("lumen-run-button")
        run_btn.set_tooltip_text("Executar arquivo atual (Ctrl+R)")
        run_btn.connect("clicked", lambda *_: self.run_current())
        self.header.pack_end(run_btn)
        self.run_btn = run_btn

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu = Gio.Menu()
        menu.append("Paleta de comandos", "win.command-palette")
        menu.append("Preferências", "win.preferences")
        menu.append("Sobre o Lumen IDE", "win.about")
        menu_btn.set_menu_model(menu)
        self.header.pack_end(menu_btn)

    def _make_traffic_handler(self, kind: str):
        def handler(_button):
            if kind == "close":
                self.close()
            elif kind == "minimize":
                self.minimize()
            elif kind == "maximize":
                if self.is_maximized():
                    self.unmaximize()
                else:
                    self.maximize()
        return handler

    def _apply_traffic_lights_preference(self) -> None:
        enabled = self.settings.get_boolean("traffic-lights") if self.settings else False
        self.traffic_box.set_visible(enabled)
        if enabled:
            self.header.add_css_class("lumen-traffic-lights")
            self.header.set_show_start_title_buttons(False)
            self.set_decorated(True)
        else:
            self.header.remove_css_class("lumen-traffic-lights")
            self.header.set_show_start_title_buttons(True)

    # ------------------------------------------------------------------ #
    # Ações
    # ------------------------------------------------------------------ #

    def _setup_actions(self) -> None:
        actions = {
            "new-file": lambda *_: self.new_tab(),
            "open-file": lambda *_: self.open_file_dialog(),
            "open-folder": lambda *_: self.sidebar._on_open_folder_clicked(None),
            "save-file": lambda *_: self.save_current(),
            "save-as": lambda *_: self.save_current_as(),
            "run-file": lambda *_: self.run_current(),
            "close-tab": lambda *_: self.close_current_tab(),
            "command-palette": lambda *_: self.show_command_palette(),
            "preferences": lambda *_: self.show_preferences(),
            "about": lambda *_: self.show_about(),
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

        app = self.get_application()
        shortcuts = {
            "win.new-file": ["<Control>n"],
            "win.open-file": ["<Control>o"],
            "win.open-folder": ["<Control><Shift>o"],
            "win.save-file": ["<Control>s"],
            "win.save-as": ["<Control><Shift>s"],
            "win.run-file": ["<Control>r", "F5"],
            "win.close-tab": ["<Control>w"],
            "win.command-palette": ["<Control><Shift>p"],
            "win.preferences": ["<Control>comma"],
        }
        for action_name, accels in shortcuts.items():
            app.set_accels_for_action(action_name, accels)

    # ------------------------------------------------------------------ #
    # Gestão de abas
    # ------------------------------------------------------------------ #

    def new_tab(self, file_path: Optional[str] = None) -> LumenEditor:
        editor = LumenEditor(file_path)
        page = self.tab_view.append(editor)
        page.set_title(editor.display_name)
        editor.connect("modified-changed", lambda _e, modified: self._update_tab_title(page, editor))
        self.tab_view.set_selected_page(page)
        return editor

    def _update_tab_title(self, page: Adw.TabPage, editor: LumenEditor) -> None:
        prefix = "● " if editor.is_modified else ""
        page.set_title(f"{prefix}{editor.display_name}")

    def _current_editor(self) -> Optional[LumenEditor]:
        page = self.tab_view.get_selected_page()
        if page is None:
            return None
        return page.get_child()

    def _on_tab_close(self, _tab_view, page: Adw.TabPage) -> bool:
        editor: LumenEditor = page.get_child()
        if editor.is_modified:
            self._confirm_close_dialog(page, editor)
            return True  # impede o fechamento imediato; o diálogo decide
        return False

    def _confirm_close_dialog(self, page: Adw.TabPage, editor: LumenEditor) -> None:
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Alterações não salvas",
            body=f"'{editor.display_name}' tem alterações não salvas. Deseja salvar antes de fechar?",
        )
        dialog.add_response("discard", "Descartar")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("save", "Salvar")
        dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("save")

        def on_response(_dlg, response: str):
            if response == "save":
                self.save_current()
                self.tab_view.close_page_finish(page, True)
            elif response == "discard":
                self.tab_view.close_page_finish(page, True)
            else:
                self.tab_view.close_page_finish(page, False)

        dialog.connect("response", on_response)
        dialog.present()

    def close_current_tab(self) -> None:
        page = self.tab_view.get_selected_page()
        if page:
            self.tab_view.close_page(page)

    # ------------------------------------------------------------------ #
    # Abrir / salvar arquivos
    # ------------------------------------------------------------------ #

    def open_file_dialog(self) -> None:
        dialog = Gtk.FileDialog(title="Abrir arquivo")
        dialog.open(self, None, self._on_file_chosen)

    def _on_file_chosen(self, dialog: Gtk.FileDialog, result) -> None:
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return
        if gfile:
            self.new_tab(gfile.get_path())

    def _on_file_activated(self, _sidebar, file_path: str) -> None:
        self.new_tab(file_path)

    def save_current(self) -> None:
        editor = self._current_editor()
        if not editor:
            return
        if editor.is_new:
            self.save_current_as()
            return
        try:
            editor.save()
        except RuntimeError as exc:
            self._show_error(str(exc))
        page = self.tab_view.get_selected_page()
        if page:
            self._update_tab_title(page, editor)

    def save_current_as(self) -> None:
        editor = self._current_editor()
        if not editor:
            return
        dialog = Gtk.FileDialog(title="Salvar como", initial_name=editor.display_name)
        dialog.save(self, None, lambda d, r: self._on_save_as_chosen(d, r, editor))

    def _on_save_as_chosen(self, dialog: Gtk.FileDialog, result, editor: LumenEditor) -> None:
        try:
            gfile = dialog.save_finish(result)
        except GLib.Error:
            return
        if gfile:
            try:
                editor.save(gfile.get_path())
            except RuntimeError as exc:
                self._show_error(str(exc))
            page = self.tab_view.get_selected_page()
            if page:
                page.set_title(editor.display_name)

    # ------------------------------------------------------------------ #
    # Execução
    # ------------------------------------------------------------------ #

    def run_current(self) -> None:
        editor = self._current_editor()
        if not editor:
            return
        if editor.is_new or editor.is_modified:
            self.save_current()
        if not editor.file_path:
            self._show_error("Salve o arquivo antes de executá-lo.")
            return
        self.terminal_panel.run_file(editor.file_path)

    # ------------------------------------------------------------------ #
    # Paleta de comandos / preferências / sobre
    # ------------------------------------------------------------------ #

    def show_command_palette(self) -> None:
        commands = [
            Command("new-file", "Novo arquivo", "Cria uma nova aba vazia", self.new_tab),
            Command("open-file", "Abrir arquivo…", "Abre um arquivo existente", self.open_file_dialog),
            Command("open-folder", "Abrir pasta de projeto…", "Define a raiz do explorador",
                    lambda: self.sidebar._on_open_folder_clicked(None)),
            Command("save-file", "Salvar", "Salva o arquivo atual", self.save_current),
            Command("run-file", "Executar arquivo atual", "Detecta a linguagem e executa", self.run_current),
            Command("preferences", "Preferências", "Aparência, fonte e linguagens", self.show_preferences),
            Command("about", "Sobre o Lumen IDE", "Versão e informações", self.show_about),
        ]
        palette = LumenCommandPalette(commands)
        palette.present(self)

    def show_preferences(self) -> None:
        prefs = LumenPreferencesWindow(settings=self.settings, transient_for=self)
        prefs.present()

    def show_about(self) -> None:
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="Lumen IDE",
            application_icon="com.lumen.ide",
            version="1.0.0",
            developer_name="Lumen IDE Contributors",
            license_type=Gtk.License.MIT_X11,
            website="https://github.com/",
            comments="Interpretador, IDE e compilador multi-linguagem para Linux,\n"
                     "com uma interface extremamente moderna inspirada na Apple.",
        )
        about.present()

    def _show_error(self, message: str) -> None:
        dialog = Adw.MessageDialog(transient_for=self, heading="Erro", body=message)
        dialog.add_response("ok", "OK")
        dialog.present()
