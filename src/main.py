# main.py
#
# Copyright 2025 Satvik Patwardhan
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

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib
from .window import LettersWindow
from .preferences import LettersPreferencesWindow
import os, sys

class LettersApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='net.codelogistics.letters',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN,
                         resource_base_path='/net/codelogistics/letters')

        # Load GSettings
        self.settings = Gio.Settings(schema_id='net.codelogistics.letters')

        self.create_action('quit', self.close_windows, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<ctrl>comma'])

        self.create_action("new_window", lambda x,y: self.get_active_window().create_window(), ["<ctrl>n"])
        self.create_action("new", lambda x, y: self.get_active_window().new_file(None), ["<ctrl>t"])
        self.create_action("close", lambda x, y: self.get_active_window().close_page(x,y), ["<ctrl>w"])
        self.create_action("open", lambda x, y: self.get_active_window().open(x,y), ["<ctrl>o"])
        self.create_action("save", lambda x, y: self.get_active_window().save(x,y), ["<ctrl>s"])
        self.create_action("save_as", lambda x, y: self.get_active_window().save_as(x,y), ["<ctrl><shift>s"])
        self.create_action("print", lambda x, y: self.get_active_window().print(x,y), ["<ctrl>p"])
        self.create_action("export", lambda x, y: self.get_active_window().export(x,y))
        self.create_action("undo", lambda x, y: self.get_active_window().run_js(None, "undo()"), ["<ctrl>z"])
        self.create_action("redo", lambda x, y: self.get_active_window().run_js(None, "redo()"), ["<ctrl>y"])
        self.create_action("underline", lambda x, y: self.get_active_window().run_js(None, "formatting.underline()"), ["<ctrl>u"])
        self.create_action("insertlink", lambda x, y: self.get_active_window().run_js(None, "formatting.createLink()"), ["<ctrl>k"])
        self.create_action("insertimage", lambda x, y: self.get_active_window().run_js(None, "insertImage()"))
        self.create_action("insertlist", lambda x, y: self.get_active_window().run_js(None, "document.execCommand('insertUnorderedList')"))

        self.create_action("strikethrough", lambda x, y: self.get_active_window().run_js(None, "formatting.strikethrough()"))
        self.create_action("highlight", lambda x, y: self.get_active_window().run_js(None, "formatting.highlight()"))
        self.create_action("indent", lambda x, y: self.get_active_window().run_js(None, "formatting.indent()"))
        self.create_action("outdent", lambda x, y: self.get_active_window().run_js(None, "formatting.outdent()"))
        self.create_action("shortcuts", self.on_shortcuts_action)

        self.files = []
        self.connect("open", self.open_files)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            if self.files:
                win = LettersWindow(application=self, opening_with_files = True)
            else:
                win = LettersWindow(application=self)
        win.present()
        if self.files:
            win.open_files(self.files)
            del self.files

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name=_('Letters'),
                                application_icon='net.codelogistics.letters',
                                developer_name='Satvik Patwardhan',
                                version='0.2.0',
                                developers=['Satvik Patwardhan'],
                                artists=["Jakub Steiner"],
                                copyright='© 2025 Satvik Patwardhan',
                                license_type=Gtk.License.GPL_3_0,
                                issue_url="https://codeberg.org/eyekay/letters/issues",
                                website="https://codeberg.org/eyekay/letters")
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        win = LettersPreferencesWindow(settings=self.settings)
        win.set_transient_for(self.props.active_window)
        win.present()

    def on_shortcuts_action(self, widget, _):
        """Callback for the app.shortcuts action."""
        from gi.repository import Adw
        shortcuts = Adw.ShortcutsDialog.new()
        # The dialog is loaded from the GResource via its UI file
        # which is included in the compiled resources
        shortcuts.set_transient_for(self.props.active_window)
        shortcuts.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def open_files(self, application, files, n_files, hint, data = None):
        self.files = files
        self.activate()

    def close_windows(self, action, data = None):
        for i in self.get_windows():
            i.close()

def main(version):
    """The application's entry point."""
    app = LettersApplication()
    return app.run(sys.argv)
