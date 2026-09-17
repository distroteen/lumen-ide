"""
application.py
===============

Classe principal Adw.Application do Lumen IDE. Carrega o CSS
customizado, inicializa o GSettings (com fallback em memória caso
o schema ainda não esteja instalado no sistema) e cria a janela
principal.
"""

from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib  # noqa: E402

from . import __app_id__
from .window import LumenWindow

_RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_settings() -> Gio.Settings:
    """
    Tenta carregar o GSettings compilado a partir do schema instalado.
    Se o schema ainda não tiver sido instalado no sistema (ex.: rodando
    a partir do código-fonte sem `glib-compile-schemas`), cai para um
    schema em memória para que o app continue funcionando.
    """
    schema_source = Gio.SettingsSchemaSource.get_default()
    schema = schema_source.lookup(__app_id__, True) if schema_source else None
    if schema is not None:
        return Gio.Settings.new(__app_id__)

    # Fallback: schema em memória (não persiste entre execuções, mas
    # evita que o app quebre em ambientes de desenvolvimento).
    memory_backend = Gio.memory_settings_backend_new()
    schema_source_local = Gio.SettingsSchemaSource.new_from_directory(
        os.path.join(_RESOURCE_DIR, "resources"),
        Gio.SettingsSchemaSource.get_default(),
        False,
    )
    local_schema = schema_source_local.lookup(__app_id__, False)
    if local_schema is None:
        # Último recurso: cria um GSettings "nulo" com valores padrão fixos.
        return _NullSettings()
    return Gio.Settings.new_full(local_schema, memory_backend, None)


class _NullSettings:
    """Objeto mínimo com a mesma interface usada pela janela, para
    garantir que o app nunca quebre mesmo sem GSettings disponível."""

    _defaults = {"traffic-lights": False, "font-size": 13}

    def get_boolean(self, key: str) -> bool:
        return bool(self._defaults.get(key, False))

    def get_int(self, key: str) -> int:
        return int(self._defaults.get(key, 0))

    def bind(self, *_args, **_kwargs) -> None:
        pass

    def connect(self, *_args, **_kwargs) -> int:
        return 0


class LumenApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self.settings = None
        self.connect("activate", self.on_activate)
        self.connect("open", self.on_open)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        self.settings = _load_settings()
        self._load_css()

    def _load_css(self) -> None:
        css_path = os.path.join(_RESOURCE_DIR, "style.css")
        if not os.path.exists(css_path):
            return
        provider = Gtk.CssProvider()
        provider.load_from_path(css_path)

        from gi.repository import Gdk
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def on_activate(self, app: "LumenApplication") -> None:
        window = self.props.active_window
        if not window:
            window = LumenWindow(settings=self.settings, application=self)
        window.present()

    def on_open(self, app: "LumenApplication", files, n_files: int, hint: str) -> None:
        window = LumenWindow(settings=self.settings, application=self)
        for gfile in files:
            path = gfile.get_path()
            if path:
                if os.path.isdir(path):
                    window.sidebar.open_folder(path)
                else:
                    window.new_tab(path)
        window.present()
