"""
preferences.py
===============

Janela de preferências do Lumen IDE (Adw.PreferencesWindow), incluindo
o toggle de "botões de tráfego estilo macOS", tamanho de fonte,
esquema de cores e a lista de linguagens disponíveis/ausentes no sistema.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio  # noqa: E402

from . import language_runner


class LumenPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "LumenPreferencesWindow"

    def __init__(self, settings: Gio.Settings | None = None, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings
        self.set_title("Preferências")

        self._build_appearance_page()
        self._build_languages_page()

    # ------------------------------------------------------------------ #

    def _build_appearance_page(self) -> None:
        page = Adw.PreferencesPage(title="Aparência", icon_name="applications-graphics-symbolic")

        group = Adw.PreferencesGroup(title="Janela", description="Ajustes visuais estilo macOS")

        traffic_row = Adw.SwitchRow(
            title="Botões de tráfego estilo macOS",
            subtitle="Mostra fechar/minimizar/maximizar como círculos coloridos à esquerda",
        )
        if self.settings:
            self.settings.bind("traffic-lights", traffic_row, "active", Gio.SettingsBindFlags.DEFAULT)
        group.add(traffic_row)

        font_row = Adw.SpinRow.new_with_range(9, 24, 1)
        font_row.set_title("Tamanho da fonte do editor")
        if self.settings:
            self.settings.bind("font-size", font_row, "value", Gio.SettingsBindFlags.DEFAULT)
        group.add(font_row)

        theme_row = Adw.ComboRow(title="Tema")
        theme_model = Gtk.StringList.new(["Sistema", "Claro", "Escuro"])
        theme_row.set_model(theme_model)
        group.add(theme_row)

        page.add(group)
        self.add(page)

    def _build_languages_page(self) -> None:
        page = Adw.PreferencesPage(title="Linguagens", icon_name="text-x-generic-symbolic")

        available_group = Adw.PreferencesGroup(
            title="Detectadas no sistema",
            description="Toolchains prontas para uso imediato",
        )
        for lang in language_runner.available_languages():
            row = Adw.ActionRow(title=lang.display_name, subtitle=", ".join(lang.extensions))
            icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
            row.add_prefix(icon)
            available_group.add(row)
        page.add(available_group)

        missing_group = Adw.PreferencesGroup(
            title="Não detectadas",
            description="Instale as ferramentas correspondentes para habilitar",
        )
        for lang in language_runner.unavailable_languages():
            missing = ", ".join(language_runner.missing_binaries(lang))
            row = Adw.ActionRow(title=lang.display_name, subtitle=f"faltando: {missing}")
            icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
            row.add_prefix(icon)
            missing_group.add(row)
        page.add(missing_group)

        self.add(page)
