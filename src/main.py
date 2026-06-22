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
import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gio, Adw
from suite_common.application import SuiteApplication

from .window import LettersWindow
from .preferences import LettersPreferencesWindow


class LettersApplication(SuiteApplication):
    """The main application singleton class.

    Migrated to SuiteApplication for shared actions (open, save, undo, redo,
    print, quit, about, preferences, shortcuts) and consistent keyboard
    shortcuts across the suite.
    """

    def __init__(self):
        super().__init__(application_id='io.github.hanthor.letters',
                         window_class=LettersWindow,
                         app_name='Letters',
                         version='0.2.0')

        # Load GSettings (Letters-specific, not in suite-common yet)
        self.settings = Gio.Settings(schema_id='io.github.hanthor.letters')

        # ── Letters-specific shortcuts ──────────────────────────────
        self._add_action('new-tab', self._on_new_tab, ['<primary>t'])

        # Formatting shortcuts
        self._add_action('underline', self._on_format, ['<primary>u'])
        self._add_action('insertlink', self._on_format, ['<primary>k'])

        # Actions without default shortcuts (toolbar-only)
        self._add_action('insertimage', self._on_format)
        self._add_action('insertlist', self._on_format)
        self._add_action('strikethrough', self._on_format)
        self._add_action('highlight', self._on_format)
        self._add_action('indent', self._on_format)
        self._add_action('outdent', self._on_format)
        self._add_action('find', self._on_find, ['<primary>f'])
        self._add_action('replace', self._on_find, ['<primary>h'])

        # Font size actions
        self._add_action('increase-font', self._on_format, ['<primary><shift>greater'])
        self._add_action('decrease-font', self._on_format, ['<primary><shift>less'])

        # Alignment actions
        self._add_action('align-left', self._on_format, ['<primary>l'])
        self._add_action('align-center', self._on_format, ['<primary>e'])
        self._add_action('align-right', self._on_format, ['<primary>r'])
        self._add_action('align-justify', self._on_format, ['<primary>j'])
        self._add_action('insert-table', self._on_insert_table)

        # Style actions for narrow toolbar and keyboard shortcuts
        style_tags = {
            'style_p': 'p', 'style_h1': 'h1', 'style_h2': 'h2',
            'style_h3': 'h3', 'style_h4': 'h4', 'style_h5': 'h5',
            'style_h6': 'h6', 'style_code': 'pre', 'style_quote': 'blockquote',
        }
        for action_name, tag in style_tags.items():
            self._add_action(action_name, lambda a, p, t=tag: self._run_js(f"applyStyle('{t}')"))

        # Add to shortcuts overlay
        self.shortcuts[_('Format')] = [
            ('<primary>b', _('Bold')),
            ('<primary>i', _('Italic')),
            ('<primary>u', _('Underline')),
            ('<primary>k', _('Insert Link')),
            ('<primary>t', _('New Tab')),
        ]
        self.shortcuts[_('Alignment')] = [
            ('<primary>l', _('Align Left')),
            ('<primary>e', _('Align Center')),
            ('<primary>r', _('Align Right')),
            ('<primary>j', _('Justify')),
        ]
        self.shortcuts[_('Font')] = [
            ('<primary><shift>greater', _('Increase Font Size')),
            ('<primary><shift>less', _('Decrease Font Size')),
        ]

        self.files = []
        self.connect('open', self._open_files)

    # ── Override suite-common actions with Letters-specific behaviour ──

    def _on_new(self, *a):
        """Ctrl+N: open a new window."""
        self.activate()

    def _on_new_tab(self, *a):
        """Ctrl+T: new tab in the current window."""
        win = self._win()
        if win and hasattr(win, 'new_file'):
            win.new_file()

    def _on_close(self, *a):
        """Ctrl+W: close the current page (or window if one page left)."""
        win = self._win()
        if win and hasattr(win, 'close_page'):
            win.close_page(None, None)

    def _on_open(self, *a):
        """Ctrl+O: open a file dialog."""
        win = self._win()
        if win and hasattr(win, 'open'):
            win.open(None, None)

    def _on_save(self, *a):
        """Ctrl+S: save the current page."""
        win = self._win()
        if win and hasattr(win, 'save'):
            win.save(None, None)

    def _on_save_as(self, *a):
        """Ctrl+Shift+S: save as a new file."""
        win = self._win()
        if win and hasattr(win, 'save_as'):
            win.save_as(None, None)

    def _on_print(self, *a):
        """Ctrl+P: export the current page."""
        win = self._win()
        if win and hasattr(win, 'export'):
            win.export(None, None)


    def _on_find(self, action, *a):
        """Ctrl+F: find. Ctrl+H: find & replace."""
        name = action.get_name()
        js = 'JSON.stringify(formatting.findText(prompt("Find:","")))' if name == 'find' else              'JSON.stringify(formatting.replaceText(prompt("Find:",""), prompt("Replace with:",""), true))'
        self._run_js(js)

    def _on_insert_table(self, *a):
        """Insert an HTML table."""
        self._run_js('formatting.insertTable(3,3)')

    def _on_undo(self, *a):
        self._run_js('undo()')

    def _on_redo(self, *a):
        self._run_js('redo()')

    # ── Letters-specific format actions ─────────────────────────────

    def _on_format(self, action, param=None):
        """Dispatch a formatting action to the active window's editor."""
        name = action.get_name()
        js_map = {
            'underline': "formatting.underline()",
            'insertlink': "formatting.createLink()",
            'insertimage': "insertImage()",
            'insertlist': "document.execCommand('insertUnorderedList')",
            'strikethrough': "formatting.strikethrough()",
            'highlight': "formatting.highlight()",
            'indent': "formatting.indent()",
            'outdent': "formatting.outdent()",
            # Font size
            'increase-font': "formatting.increaseFontSize()",
            'decrease-font': "formatting.decreaseFontSize()",
            # Alignment
            'align-left': "formatting.alignLeft()",
            'align-center': "formatting.alignCenter()",
            'align-right': "formatting.alignRight()",
            'align-justify': "formatting.alignJustify()",
        }
        js = js_map.get(name)
        if js:
            self._run_js(js)

    def _run_js(self, js):
        """Run JavaScript in the active window's focused webview."""
        win = self._win()
        if win and hasattr(win, 'run_js'):
            win.run_js(None, js)

    # ── Preferences ─────────────────────────────────────────────────

    def _on_preferences(self, *args):
        """Override to use LettersPreferencesWindow with settings."""
        win = LettersPreferencesWindow(settings=self.settings)
        win.set_transient_for(self.props.active_window)
        win.present()

    # ── Lifecycle ───────────────────────────────────────────────────

    def do_activate(self):
        win = self.props.active_window
        if not win:
            if self.files:
                win = LettersWindow(application=self, opening_with_files=True)
            else:
                win = LettersWindow(application=self)
        win.present()
        if self.files:
            win.open_files(self.files)
            del self.files

    def _open_files(self, application, files, n_files, hint, data=None):
        self.files = files
        self.activate()


def main(version):
    """The application's entry point."""
    app = LettersApplication()
    return app.run(sys.argv)
