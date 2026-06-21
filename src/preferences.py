# preferences.py
#
# Copyright 2026 Satvik Patwardhan & Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib

FORMAT_MAP = ["odt", "docx", "md", "html", "txt", "rtf"]

@Gtk.Template(resource_path='/net/codelogistics/letters/preferences.ui')
class LettersPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'LettersPreferencesWindow'

    default_format_row = Gtk.Template.Child()
    font_row = Gtk.Template.Child()
    editor_margin_row = Gtk.Template.Child()
    spell_check_row = Gtk.Template.Child()
    auto_save_row = Gtk.Template.Child()
    show_toolbar_row = Gtk.Template.Child()

    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self._settings = settings
        self._saving = False

        # Load current settings into UI
        self._load_settings()

        # Connect change signals
        self.default_format_row.connect("notify::selected", self._on_format_changed)
        self.font_row.connect("notify::text", self._on_font_changed)
        self.editor_margin_row.connect("notify::value", self._on_margin_changed)
        self.spell_check_row.connect("notify::active", self._on_spellcheck_changed)
        self.auto_save_row.connect("notify::value", self._on_autosave_changed)
        self.show_toolbar_row.connect("notify::active", self._on_toolbar_changed)

    def _load_settings(self):
        """Read GSettings and update UI widgets."""
        format_val = self._settings.get_string("default-format")
        if format_val in FORMAT_MAP:
            self.default_format_row.set_selected(FORMAT_MAP.index(format_val))

        font = self._settings.get_string("font")
        if font:
            self.font_row.set_text(font)

        margin = self._settings.get_double("editor-margin")
        self.editor_margin_row.set_value(margin)

        self.spell_check_row.set_active(self._settings.get_boolean("spell-check-enabled"))
        self.auto_save_row.set_value(self._settings.get_int("auto-save-interval"))
        self.show_toolbar_row.set_active(self._settings.get_boolean("show-toolbar"))

    def _on_format_changed(self, row, _pspec):
        if self._saving: return
        selected = row.get_selected()
        if 0 <= selected < len(FORMAT_MAP):
            self._settings.set_string("default-format", FORMAT_MAP[selected])

    def _on_font_changed(self, row, _pspec):
        if self._saving: return
        text = row.get_text().strip()
        self._settings.set_string("font", text)

    def _on_margin_changed(self, row, _pspec):
        if self._saving: return
        self._settings.set_double("editor-margin", row.get_value())

    def _on_spellcheck_changed(self, row, _pspec):
        if self._saving: return
        self._settings.set_boolean("spell-check-enabled", row.get_active())

    def _on_autosave_changed(self, row, _pspec):
        if self._saving: return
        self._settings.set_int("auto-save-interval", int(row.get_value()))

    def _on_toolbar_changed(self, row, _pspec):
        if self._saving: return
        self._settings.set_boolean("show-toolbar", row.get_active())
