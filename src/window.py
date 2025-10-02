# window.py
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

import gi
gi.require_version('WebKit', '6.0')
from gi.repository import Gio, Adw, Gtk, WebKit

import os
import pypandoc, weasyprint

@Gtk.Template(resource_path='/net/codelogistics/letters/window.ui')
class LettersWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'LettersWindow'

    tbview = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    tabbar = Gtk.Template.Child()
    tabview = Gtk.Template.Child()
    statuspage = Gtk.Template.Child()
    add_button = Gtk.Template.Child()
    toolbar = Gtk.Template.Child()

    bold_button = Gtk.Template.Child()
    italic_button = Gtk.Template.Child()
    underline_button = Gtk.Template.Child()
    list_button = Gtk.Template.Child()
    link_button = Gtk.Template.Child()
    image_button = Gtk.Template.Child()
    styles_dropdown = Gtk.Template.Child()

    FORCE_CLOSE = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("close-request", self.close_window)

        self.toolbar.set_visible(False)
        self.stack.set_visible_child(self.statuspage)
        self.tbview.set_top_bar_style(Adw.ToolbarStyle.FLAT)

        self.add_button.connect("clicked", self.new_file)
        self.tabview.connect("close-page", self.page_closing)
        self.tabview.connect("notify::selected-page", self.update_title)
        self.tabview.connect("create-window", self.create_window)
        self.tabview.connect("page-attached", self.new_page)

        self.bold_button.connect('clicked', lambda btn: self.get_application().get_active_window().run_js(None, "formatting.bold()"))
        self.italic_button.connect('clicked', lambda btn: self.get_application().get_active_window().run_js(None, "formatting.italic()"))
        self.underline_button.connect('clicked', lambda btn: self.get_application().get_active_window().run_js(None, "formatting.underline()"))
        self.list_button.connect('clicked', lambda btn: self.get_application().get_active_window().run_js(None, "document.execCommand('insertUnorderedList')"))
        self.link_button.connect('clicked', lambda btn: self.get_application().get_active_window().run_js(None, "formatting.createLink()"))
        self.image_button.connect('clicked', lambda btn: self.get_application().get_active_window().run_js(None, "insertImage()"))
        self.styles_dropdown.connect("notify::selected", lambda dropdown, _: self.get_application().get_active_window().on_style_dropdown_changed(None, dropdown))

    # ---------------------------------- GTK/ FRONTEND RELATED FUNCTIONS ---------------------------

    def new_file(self, button = None):
        page = self.tabview.append(self.new_webview())
        page.set_title(_("Untitled Document"))
        page.get_child().fresh = True # newly open blank page should not trigger save file dialog when being closed
        page.closing_after_save = False
        self.update_title()
        self.toolbar.set_visible(True)
        self.stack.set_visible_child(self.tabview)
        self.tbview.set_top_bar_style(Adw.ToolbarStyle.RAISED)

    def on_context_menu(self, webview, context_menu, hit_test_result):
        if hit_test_result.context_is_link():
            for i in range(5):
                if i == 3: #copy link location
                    continue

                context_menu.remove(context_menu.get_items()[i])
            context_menu.remove(context_menu.get_items()[0])

        elif hit_test_result.context_is_image():
            import json
            image_url = hit_test_result.get_image_uri()
            safe_url = json.dumps(image_url)
            js_code = f"""
            (function() {{
                const img = document.querySelector("img[src='"+{safe_url}+"']");
                if (img) resizeImg(img);
            }})()
            """
            action = Gio.SimpleAction.new("resize_image", None)
            action.connect("activate", lambda a, p: self.run_js(webview, js_code))

            context_menu_item = WebKit.ContextMenuItem.new_from_gaction(action, "Resize Image", None)
            context_menu.insert(context_menu_item, 0)
        return

    def open(self, action, data = None):
        def open_callback(dialog, result, data = None):
            try:
                file = open_dialog.open_finish(result)
                if file.get_basename().rpartition(".")[2] not in ["docx", "odt", "txt", "md", "html"]:
                    dialog = Adw.AlertDialog()
                    dialog.set_heading(_("Unsupported File Format"))
                    dialog.set_body(_("The file you selected could not be opened as it is in an unrecognised format."))
                    dialog.add_response("ok", _("OK"))
                    dialog.set_default_response("ok")
                    dialog.choose(self)
                    return
                else:
                    webview = self.new_webview(file.get_path())
                    webview.fresh = False
                    page = self.tabview.append(webview)
                    page.set_title(file.get_basename())
                    page.set_needs_attention(False)
                    page.closing_after_save = False
                    self.update_title()
                    self.toolbar.set_visible(True)
                    self.stack.set_visible_child(self.tabview)
                    self.tbview.set_top_bar_style(Adw.ToolbarStyle.RAISED)
            except Exception as e:
                print(e)
        open_dialog = Gtk.FileDialog()
        open_dialog.open(self, None, open_callback, None)
        self.update_title()

    def new_page(self, tabview, pos, data=None):
        self.update_title()
        self.toolbar.set_visible(True)
        self.stack.set_visible_child(self.tabview)
        self.tbview.set_top_bar_style(Adw.ToolbarStyle.RAISED)

    def close_page(self, action, data = None):
        if self.tabview.get_n_pages():
            self.tabview.close_page(self.tabview.get_selected_page())
        elif self.toolbar.get_visible(): # a tab was just closed
            self.toolbar.set_visible(False)
        else:
            self.get_application().remove_window(self)
            self.close()

    def page_closing(self, view, page, data = None):
        if page.get_needs_attention(): # using get_needs_attention as a way to check save state
            def choose_callback(dialog, result):
                try:
                    response = confirm_dialog.choose_finish(result)
                    if response == "cancel":
                        self.tabview.close_page_finish(page, False)
                    if response == "save":
                        self.save(None)
                        page.closing_after_save = True
                    elif response == "discard":
                        self.tabview.close_page_finish(page, True)
                        page.get_child().terminate_web_process()
                        if view.get_n_pages() <= 1: # after the last page is closed, get_n_pages() returns 1 for some reason
                            self.stack.set_visible_child(self.statuspage)
                            self.tbview.set_top_bar_style(Adw.ToolbarStyle.FLAT)
                            self.toolbar.set_visible(False)
                except Exception as e:
                    print(e)
                    self.tabview.close_page_finish(page, False)
            confirm_dialog = Adw.AlertDialog()
            confirm_dialog.set_heading(_("Save document?"))
            confirm_dialog.set_body(page.get_title() + _("\n This document has not been saved. Changes which are not saved will be permanently lost."))
            confirm_dialog.add_response("cancel", _("_Cancel"))
            confirm_dialog.add_response("discard", _("_Discard"))
            confirm_dialog.add_response("save", _("_Save"))
            confirm_dialog.set_close_response("cancel")
            confirm_dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
            confirm_dialog.set_response_appearance("cancel", Adw.ResponseAppearance.DESTRUCTIVE)
            confirm_dialog.choose(self, None, choose_callback)
            return True
        else:
            self.tabview.close_page_finish(page, True)
            page.get_child().terminate_web_process()
            if not view.get_n_pages():
                self.stack.set_visible_child(self.statuspage)
                self.toolbar.set_visible(False)
                self.tbview.set_top_bar_style(Adw.ToolbarStyle.FLAT)

    def create_window(self, tabview=None):
        new_window = LettersWindow(application = self.get_application())
        new_window.present()
        return new_window.tabview

    def close_window(self, window):
        if self.FORCE_CLOSE:
            return False
        dirty_pages = [
            self.tabview.get_nth_page(i)
            for i in range(self.tabview.get_n_pages())
            if self.tabview.get_nth_page(i).get_needs_attention()
        ]

        if not dirty_pages:
            return False

        dialog = Adw.AlertDialog()
        dialog.set_heading(_("Unsaved changes"))
        body_lines = [_("The following documents have unsaved changes:")]
        body_lines += [f"• {p.get_title()}" for p in dirty_pages]
        body_lines += [_("All unsaved changes will be discarded if you close Letters now.")]
        dialog.set_body("\n".join(body_lines))

        dialog.add_response("cancel", _("_Cancel"))
        dialog.add_response("discard", _("_Discard All"))
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.set_response_appearance("cancel", Adw.ResponseAppearance.DESTRUCTIVE)

        def dialog_callback(d, result):
            try:
                resp = d.choose_finish(result)
                if resp == "cancel":
                    return

                if resp == "discard":
                    self.FORCE_CLOSE = True
                    self.close()
                    return

            except Exception as e:
                print(e)

        dialog.choose(self, None, dialog_callback)
        return True

    def update_title(self, tabview = None, data = None):
        page = self.tabview.get_selected_page()
        if page:
            if page.get_needs_attention():
                self.set_title(page.get_title() + " (*) - Letters")
            else:
                self.set_title(page.get_title() + " - Letters")
        else:
            self.set_title(_("Letters"))

    # --------------------------------- WEBKIT RELATED FUNCTIONS ----------------------------------------------------

    def new_webview(self, file_path = None):
        # Returns a WebKit.WebView() with style change handlers registered
        webview = WebKit.WebView()

        settings = webview.get_settings()
        settings.set_enable_developer_extras(True)

        ucm = webview.get_user_content_manager()
        ucm.register_script_message_handler("styleChange")
        ucm.register_script_message_handler("inlineStyleChange")
        ucm.register_script_message_handler("contentChanged")
        ucm.connect("script-message-received::styleChange", lambda ucm, msg: self.get_application().get_active_window().on_style_change_from_js(ucm, msg))
        ucm.connect("script-message-received::inlineStyleChange", lambda ucm, msg: self.get_application().get_active_window().on_inline_style_change_from_js(ucm, msg))
        ucm.connect("script-message-received::contentChanged", lambda ucm, msg: self.get_application().get_active_window().on_content_changed(ucm, msg, webview))

        webview.connect("context-menu", self.on_context_menu)
        webview.connect('load-changed', self.load_changed)

        if file_path:
            webview.file_path = file_path
            if not file_path.endswith(('.txt', '.html')):
                try:
                    content = pypandoc.convert_file(file_path, 'html', extra_args=['--embed-resources', '--sandbox'])
                except Exception as e:
                    content = f"<p>Error loading file: {e}</p>"
            else:
                with open(file_path, 'r') as f:
                        content = f.read()
        else:
            webview.file_path = ""
            content = '<!DOCTYPE html><html><head></head><body><p></p></body></html>'

        webview.load_html(content)
        return webview

    def run_js(self, webview, code):
        if not webview: # detect current webview
            webview = self.tabview.get_selected_page().get_child()
        webview.evaluate_javascript(code, -1, None, None, None, None)

    def save(self, action, data = None):
        page = self.tabview.get_selected_page()
        if not page or not page.get_needs_attention():
            return
        else:
            webview = page.get_child()
            if webview.file_path: # opened file, edited
                self.save_out(webview, webview.file_path)
            else: # new file
                def save_callback(dialog, result):
                    try:
                        file = save_dialog.save_finish(result)
                        self.save_out(webview, file.get_path())
                    except Exception as e:
                        self.tabview.close_page_finish(page, False)

                save_dialog = Gtk.FileDialog()
                filters_list = Gio.ListStore()
                for i in ['odt', 'docx', 'txt', 'md', 'html']:
                    save_filter = Gtk.FileFilter()
                    save_filter.add_suffix(i)
                    filters_list.append(save_filter)
                save_dialog.set_filters(filters_list)
                save_dialog.set_initial_name("Untitled Document.odt")
                save_dialog.save(self.get_application().get_active_window(), None, save_callback)

    def save_as(self, action, data = None):
        page = self.tabview.get_selected_page()
        if not page:
            return
        webview = page.get_child()
        def save_callback(dialog, result):
            try:
                file = save_dialog.save_finish(result)
                self.save_out(webview, file.get_path())
            except Exception as e:
                print(e)

        save_dialog = Gtk.FileDialog()
        filters_list = Gio.ListStore()
        for i in ['odt', 'docx', 'txt', 'md', 'html']:
            save_filter = Gtk.FileFilter()
            save_filter.add_suffix(i)
            filters_list.append(save_filter)
        save_dialog.set_filters(filters_list)
        if webview.file_path:
            save_dialog.set_initial_name(os.path.basename(webview.file_path))
        else:
            save_dialog.set_initial_name("Untitled Document.odt")
        save_dialog.save(self.get_application().get_active_window(), None, save_callback)

    def save_out(self, webview, file_path):
        def output_callback(webview, result, data=None):
            page = self.tabview.get_page(webview)
            try:
                content = webview.evaluate_javascript_finish(result).to_string()
                ext = file_path.rpartition('.')[2]
                if ext not in ['odt', 'docx', 'txt', 'md', 'html']:
                    ext = "odt"
                try:
                    pypandoc.convert_text(content, ext, format='html', outputfile=file_path, extra_args=['--embed-resources', '--sandbox'])

                    page.set_needs_attention(False)
                    page.set_title(os.path.basename(file_path))
                    self.update_title()
                    webview.file_path = file_path
                    if page.closing_after_save:
                        self.tabview.close_page_finish(page, True)
                        webview.terminate_web_process()
                except Exception as e:
                    print(_("Error saving file: "), e)
                    self.tabview.close_page_finish(page, False)
            except Exception as e:
                print(_("Error saving file: "), e)
                self.tabview.close_page_finish(page, False)

        webview.evaluate_javascript("document.documentElement.outerHTML", -1, None, None, None, output_callback)

    def print(self, action, data = None):
        if self.tabview.get_selected_page():
            self.run_js(self.tabview.get_selected_page().get_child(), "printPage()")

    def export(self, action, data = None):
        page = self.tabview.get_selected_page()
        if not page:
            return
        webview = page.get_child()
        def save_callback(dialog, result):
            try:
                file = save_dialog.save_finish(result)
                self.export_out(webview, file.get_path())
            except Exception as e:
                print(e)

        save_dialog = Gtk.FileDialog()
        filters_list = Gio.ListStore()
        save_filter = Gtk.FileFilter()
        save_filter.add_suffix('pdf')
        filters_list.append(save_filter)
        save_dialog.set_filters(filters_list)
        if webview.file_path:
            save_dialog.set_initial_name(os.path.basename(webview.file_path))
        else:
            save_dialog.set_initial_name("Untitled Document.pdf")
        save_dialog.save(self.get_application().get_active_window(), None, save_callback)

    def export_out(self, webview, file_path):
        def output_callback(webview, result, data=None):
            page = self.tabview.get_page(webview)
            try:
                content = webview.evaluate_javascript_finish(result).to_string()
                from pathlib import Path
                base_dir = Path(__file__).parent
                with open(base_dir / "styles.css", "r") as f:
                    css = f.read()
                settings = Gtk.Settings.get_default()
                font_css = ":root {color-scheme: light dark} body {font-family: \"" + settings.get_property('gtk-font-name').rstrip(' 0123456789') + "\"}"
                try:
                    weasyprint.HTML(string=content).write_pdf(file_path, stylesheets=[weasyprint.CSS(string=css), weasyprint.CSS(string=font_css)])

                except Exception as e:
                    print(_("Error exporting file: "), e)
            except Exception as e:
                print(_("Error exporting file: "), e)

        webview.evaluate_javascript("document.documentElement.outerHTML", -1, None, None, None, output_callback)

    def load_changed(self, webview, load_event):
        if load_event == 3:
            self.run_js(webview, "document.body.contentEditable = true;")

            from pathlib import Path
            base_dir = Path(__file__).parent
            js_path = base_dir / "editor.js"
            with open(js_path, "r") as f:
                js_code = f.read()
            self.run_js(webview, js_code)
            self.run_js(webview, "loadCSS(\"styles.css\")")

            settings = Gtk.Settings.get_default()
            font = settings.get_property('gtk-font-name').rstrip(' 0123456789')

            style_sheet = WebKit.UserStyleSheet(":root {color-scheme: light dark} body {font-family: \"" + font + "\"; margin-left:16%; margin-right:16%;}", 0, 0, None, None)
            webview.get_user_content_manager().add_style_sheet(style_sheet)

            cursor_js = """
            (function() {
                const firstElem = document.body.querySelector('p, h1, h2, h3, h4, h5, h6, pre, blockquote');
                if (firstElem) {
                    firstElem.focus();
                    const sel = window.getSelection();
                    const range = document.createRange();

                    if (firstElem.childNodes.length === 0) {
                        firstElem.appendChild(document.createTextNode('\\u200b'));
                    }

                    range.setStart(firstElem.firstChild, 0);
                    range.collapse(true);

                    sel.removeAllRanges();
                    sel.addRange(range);
                }
            })();
            """
            self.run_js(webview, cursor_js)
            self.tabview.get_page(webview).set_needs_attention(False)

    def on_style_dropdown_changed(self, webview, dropdown):
        style = dropdown.get_model()[dropdown.get_selected()].get_string()
        styles_tag = {_("Paragraph"): 'p', _("Heading 1"): 'h1', _("Heading 2"): 'h2', _("Heading 3"): 'h3', _("Heading 4"): 'h4', _("Heading 5"): 'h5', _("Heading 6"): 'h6', _("Code"): 'pre', _("Quote"): 'blockquote'}

        self.run_js(webview, f"applyStyle('{styles_tag[style]}')")

    def on_style_change_from_js(self, ucm, msg):
        style = msg.to_string()
        if not style:
            return
        styles_int = {'p': 0, 'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6, 'pre': 7, 'blockquote' : 8}
        if style not in styles_int:
            style = 'p'
        self.styles_dropdown.set_selected(styles_int[style])

    def on_inline_style_change_from_js(self, ucm, msg):
        try:
            import json
            styles = json.loads(msg.to_json(0))
        except Exception as e:
            return

        self.italic_button.set_active(bool(styles.get("italic", False)))
        self.bold_button.set_active(bool(styles.get("bold", False)))
        self.underline_button.set_active(bool(styles.get("underline", False)))
        self.list_button.set_active(bool(styles.get("list", False)))

    def on_content_changed(self, ucm, msg, webview):
        if webview.fresh:
            self.tabview.get_page(webview).set_needs_attention(False)
            webview.fresh = False
        else:
            self.tabview.get_page(webview).set_needs_attention(True)
        self.update_title()
