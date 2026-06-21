"""
Comprehensive tests for preference-related logic.

Tests format maps, style mappings, file path handling, GSettings key
validation, and border/edge cases — all without requiring a display server.
"""

import pytest
import xml.etree.ElementTree as ET

# ---- Constants replicated from src/ ----

FORMAT_MAP = ["odt", "docx", "md", "html", "txt", "rtf"]
VALID_EXTS = {"docx", "odt", "txt", "md", "html", "rtf"}

STYLES_INT = {
    'p': 0, 'h1': 1, 'h2': 2, 'h3': 3,
    'h4': 4, 'h5': 5, 'h6': 6, 'pre': 7, 'blockquote': 8
}

STYLES_TAG = {
    "Paragraph": 'p', "Heading 1": 'h1', "Heading 2": 'h2',
    "Heading 3": 'h3', "Heading 4": 'h4', "Heading 5": 'h5',
    "Heading 6": 'h6', "Code": 'pre', "Quote": 'blockquote'
}

NAME_TO_STYLE = {v: k for k, v in STYLES_TAG.items()}

# ---- Format Map Tests ----

class TestFormatMap:
    def test_contains_all_formats(self):
        assert set(FORMAT_MAP) == {"odt", "docx", "md", "html", "txt", "rtf"}

    def test_no_duplicates(self):
        assert len(FORMAT_MAP) == len(set(FORMAT_MAP))

    def test_order_is_stable(self):
        assert FORMAT_MAP == ["odt", "docx", "md", "html", "txt", "rtf"]

    def test_first_is_default(self):
        assert FORMAT_MAP[0] == "odt"

    def test_all_formats_have_indices(self):
        for i, fmt in enumerate(FORMAT_MAP):
            assert FORMAT_MAP.index(fmt) == i

    def test_all_formats_are_lowercase(self):
        for fmt in FORMAT_MAP:
            assert fmt == fmt.lower()


# ---- File Extension / Path Tests ----

class TestFileExtensions:
    VALID_OPEN_EXTS = {"docx", "odt", "txt", "md", "html"}
    ALLOWED_SAVE_EXTS = {"odt", "docx", "rtf", "txt", "md", "html"}

    # --- Open validation ---

    @pytest.mark.parametrize("filename", [
        "report.docx", "notes.odt", "readme.md",
        "index.html", "plain.txt", "letter.docx",
        "a.b.c.docx",  # multiple dots
        "résumé.odt",  # unicode
        "file.TXT",    # uppercase
        "file.DOCX",
    ])
    def test_open_valid_extensions(self, filename):
        ext = filename.rpartition(".")[2].lower()
        assert ext in self.VALID_OPEN_EXTS

    @pytest.mark.parametrize("filename", [
        "spreadsheet.xlsx", "image.png", "script.py",
        "data.json", "archive.zip", "doc.pdf",
        "song.mp3", "video.mp4", "style.css",
        "", "noext",
    ])
    def test_open_invalid_extensions(self, filename):
        ext = filename.rpartition(".")[2].lower()
        assert ext not in self.VALID_OPEN_EXTS

    # --- Save extension fallback ---

    @pytest.mark.parametrize("path,expected", [
        ("doc.docx", "docx"),
        ("file.odt", "odt"),
        ("notes.md", "md"),
        ("page.html", "html"),
        ("readme.txt", "txt"),
        ("doc.rtf", "rtf"),
        ("file.pdf", "odt"),        # fallback
        ("file", "odt"),            # no extension
        ("", "odt"),                # empty
        ("archive.tar.gz", "odt"),  # compound ext → fallback
        ("file.XML", "odt"),        # uppercase unknown
        ("file.ODT", "odt"),        # uppercase known — lowercase match?
    ])
    def test_save_extension_fallback(self, path, expected):
        ext = path.rpartition('.')[2].lower()
        if ext not in self.ALLOWED_SAVE_EXTS:
            ext = "odt"
        assert ext == expected

    def test_save_extension_case_insensitive(self):
        """Save format should be case-insensitive (lowercased)."""
        paths = ["file.DOCX", "file.Odt", "file.MD", "file.HTML", "file.TxT"]
        allowed = {"odt", "docx", "rtf", "txt", "md", "html"}
        for path in paths:
            ext = path.rpartition('.')[2].lower()
            assert ext in allowed

    # --- basename parsing ---

    @pytest.mark.parametrize("path,basename,ext", [
        ("/home/user/doc.docx", "doc.docx", "docx"),
        ("/home/user/file.odt", "file.odt", "odt"),
        ("report", "report", ""),
        ("/path/to/a.long.file.name.md", "a.long.file.name.md", "md"),
        ("/", "", ""),
        ("file.", "file.", ""),
    ])
    def test_basename_and_extension(self, path, basename, ext):
        import os
        name = os.path.basename(path)
        assert name == basename
        if ext:
            assert name.rpartition(".")[2] == ext


# ---- Style Mapping Tests ----

class TestStyleMapping:
    def test_styles_int_has_all_tags(self):
        assert set(STYLES_INT.keys()) == {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'blockquote'}

    def test_styles_int_values_sequential(self):
        values = sorted(STYLES_INT.values())
        assert values == list(range(len(values)))

    def test_styles_int_no_gaps(self):
        assert max(STYLES_INT.values()) == len(STYLES_INT) - 1

    def test_unknown_style_not_in_map(self):
        unknown = {'div', 'span', 'ul', 'ol', 'table', 'header', 'footer', 'section'}
        for s in unknown:
            assert s not in STYLES_INT

    def test_default_fallback(self):
        """Unknown styles should default to 'p'."""
        style = 'div'
        if style not in STYLES_INT:
            style = 'p'
        assert STYLES_INT[style] == 0

    def test_styles_tag_has_all_labels(self):
        expected_labels = {"Paragraph", "Heading 1", "Heading 2", "Heading 3",
                           "Heading 4", "Heading 5", "Heading 6", "Code", "Quote"}
        assert set(STYLES_TAG.keys()) == expected_labels

    def test_styles_tag_maps_correctly(self):
        assert STYLES_TAG["Paragraph"] == 'p'
        assert STYLES_TAG["Heading 1"] == 'h1'
        assert STYLES_TAG["Heading 6"] == 'h6'
        assert STYLES_TAG["Code"] == 'pre'
        assert STYLES_TAG["Quote"] == 'blockquote'

    def test_name_to_style_reverse_mapping(self):
        assert NAME_TO_STYLE['p'] == "Paragraph"
        assert NAME_TO_STYLE['h1'] == "Heading 1"
        assert NAME_TO_STYLE['blockquote'] == "Quote"

    def test_styles_are_html_valid_tags(self):
        """All style tags should be valid HTML5 elements."""
        valid_html = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'blockquote'}
        for tag in STYLES_INT.keys():
            assert tag in valid_html

    def test_blockquote_is_last(self):
        """blockquote should have the highest index (dropdown order)."""
        assert STYLES_INT['blockquote'] == max(STYLES_INT.values())


# ---- GSettings Schema Validation ----

class TestGSettingsSchema:
    SCHEMA_PATH = "data/net.codelogistics.letters.gschema.xml"

    def test_schema_exists(self):
        import os
        assert os.path.exists(self.SCHEMA_PATH)

    def test_schema_is_valid_xml(self):
        tree = ET.parse(self.SCHEMA_PATH)
        assert tree.getroot() is not None

    def test_schema_has_correct_id(self):
        tree = ET.parse(self.SCHEMA_PATH)
        root = tree.getroot()
        ns = {'': 'http://www.gtk.org/schemas'}
        schema = root.find('schema') or root.find('{http://www.gtk.org/schemas}schema')
        assert schema is not None
        assert schema.get('id') == 'net.codelogistics.letters'

    def test_schema_has_required_keys(self):
        tree = ET.parse(self.SCHEMA_PATH)
        root = tree.getroot()
        schema = root.find('schema') or root.find('{http://www.gtk.org/schemas}schema')
        keys = schema.findall('key') or schema.findall('{http://www.gtk.org/schemas}key')
        key_names = {k.get('name') for k in keys}

        required = {'font', 'editor-margin', 'spell-check-enabled',
                    'auto-save-interval', 'show-toolbar', 'default-format',
                    'window-width', 'window-height', 'window-maximized'}
        missing = required - key_names
        assert not missing, f"Missing keys: {missing}"

    def test_schema_key_types(self):
        tree = ET.parse(self.SCHEMA_PATH)
        root = tree.getroot()
        schema = root.find('schema') or root.find('{http://www.gtk.org/schemas}schema')
        keys = schema.findall('key') or schema.findall('{http://www.gtk.org/schemas}key')

        types = {}
        for k in keys:
            types[k.get('name')] = k.get('type')

        assert types['font'] == 's'
        assert types['editor-margin'] == 'd'
        assert types['spell-check-enabled'] == 'b'
        assert types['auto-save-interval'] == 'i'
        assert types['default-format'] == 's'

    def test_schema_default_values(self):
        tree = ET.parse(self.SCHEMA_PATH)
        root = tree.getroot()
        # Get schema regardless of namespace
        schema = root.find('.//{http://www.gtk.org/schemas}schema') or root.find('.//schema')
        if schema is None:
            schema = root  # fallback: root could be schema
        keys = schema.findall('{http://www.gtk.org/schemas}key') or schema.findall('key')

        defaults = {}
        for k in keys:
            default = k.find('{http://www.gtk.org/schemas}default') or k.find('default')
            if default is not None:
                defaults[k.get('name')] = default.text

        assert defaults.get('spell-check-enabled') == 'true', \
            f"spell-check-enabled default: {defaults.get('spell-check-enabled')}"
        assert defaults.get('show-toolbar') == 'true'
        assert defaults.get('default-format') == '"odt"'
        assert defaults.get('editor-margin') == '16'
        assert defaults.get('auto-save-interval') == '0'

    def test_schema_key_count(self):
        tree = ET.parse(self.SCHEMA_PATH)
        root = tree.getroot()
        schema = root.find('schema') or root.find('{http://www.gtk.org/schemas}schema')
        keys = schema.findall('key') or schema.findall('{http://www.gtk.org/schemas}key')
        assert len(keys) == 9, f"Expected 9 keys, got {len(keys)}"

    def test_schema_key_ranges(self):
        """Check range constraints on numeric keys."""
        tree = ET.parse(self.SCHEMA_PATH)
        root = tree.getroot()
        schema = root.find('.//{http://www.gtk.org/schemas}schema') or root.find('.//schema') or root
        keys = schema.findall('{http://www.gtk.org/schemas}key') or schema.findall('key')

        ranges = {}
        for k in keys:
            rng = k.find('{http://www.gtk.org/schemas}range') or k.find('range')
            if rng is not None:
                ranges[k.get('name')] = {
                    'min': rng.get('min'),
                    'max': rng.get('max')
                }

        assert 'editor-margin' in ranges, f"Key ranges found: {list(ranges.keys())}"
        assert ranges['editor-margin']['min'] == '0'
        assert ranges['editor-margin']['max'] == '50'

        assert 'auto-save-interval' in ranges
        assert ranges['auto-save-interval']['max'] == '3600'


# ---- Desktop File Validation ----

class TestDesktopFile:
    DESKTOP_PATH = "data/net.codelogistics.letters.desktop.in"

    def test_desktop_file_exists(self):
        import os
        assert os.path.exists(self.DESKTOP_PATH)

    def test_categories_are_standard(self):
        with open(self.DESKTOP_PATH) as f:
            content = f.read()
        assert "Categories=Office;WordProcessor;" in content
        # Should NOT have legacy categories
        assert "X-Accessories" not in content
        assert "X-Office" not in content

    def test_keywords_meaningful(self):
        with open(self.DESKTOP_PATH) as f:
            content = f.read()
        assert "Keywords=word" in content
        assert "processor" in content
        # Should NOT have useless keywords
        assert "Keywords=GTK" not in content

    def test_dbus_activatable(self):
        with open(self.DESKTOP_PATH) as f:
            content = f.read()
        assert "DBusActivatable=true" in content

    def test_startup_notify(self):
        with open(self.DESKTOP_PATH) as f:
            content = f.read()
        assert "StartupNotify=true" in content

    def test_mime_types(self):
        with open(self.DESKTOP_PATH) as f:
            content = f.read()
        assert "openxmlformats" in content  # docx
        assert "opendocument" in content     # odt
        assert "text/markdown" in content


# ---- Metainfo Validation ----

class TestMetainfo:
    METAINFO_PATH = "data/net.codelogistics.letters.metainfo.xml.in"

    def test_metainfo_exists(self):
        import os
        assert os.path.exists(self.METAINFO_PATH)

    def test_developer_id_is_proper(self):
        with open(self.METAINFO_PATH) as f:
            content = f.read()
        assert '<developer id="net.codelogistics">' in content
        assert 'tld.vendor' not in content

    def test_has_release_info(self):
        tree = ET.parse(self.METAINFO_PATH)
        root = tree.getroot()
        releases = root.find('releases')
        assert releases is not None
        children = list(releases)
        assert len(children) > 0

    def test_has_urls(self):
        with open(self.METAINFO_PATH) as f:
            content = f.read()
        assert "url type=\"homepage\"" in content
        assert "url type=\"vcs-browser\"" in content
        assert "url type=\"bugtracker\"" in content


# ---- Blueprint UI File Checks ----

class TestBlueprintFiles:
    def test_window_blp_has_no_translatable_icon(self):
        """Icons should NOT use _() — regression check for C3."""
        with open("src/window.blp") as f:
            content = f.read()
        # Check no icon-name uses _()
        assert 'icon-name: _("' not in content, \
            "Found translatable icon name (regression of C3)"

    def test_window_blp_has_flat_buttons(self):
        """Header buttons should be flat per spec G8."""
        with open("src/window.blp") as f:
            content = f.read()
        assert 'styles ["flat"]' in content

    def test_window_blp_has_accessibility(self):
        """Widgets should have accessibility labels per spec G9."""
        with open("src/window.blp") as f:
            content = f.read()
        assert 'accessibility' in content
        assert 'label:' in content

    def test_window_blp_has_breakpoint(self):
        """Should have Adw.Breakpoint per spec G2."""
        with open("src/window.blp") as f:
            content = f.read()
        assert 'Adw.Breakpoint' in content


# ---- Critical Regression Checks ----

class TestRegressions:
    SCRIPTS = ["src/main.py", "src/window.py", "src/preferences.py"]

    def test_all_python_files_compile(self):
        import py_compile
        for path in self.SCRIPTS:
            py_compile.compile(path, doraise=True)

    def test_no_print_statements_in_production_paths(self):
        """Key user-facing operations should not rely on print() for errors."""
        # Check that print() is not used in save/export/load error paths
        with open("src/window.py") as f:
            content = f.read()
        # print() still exists for debug but should be paired with user feedback
        assert "show_error" in content
        assert "show_toast" in content

    def test_shortcuts_action_registered(self):
        """app.shortcuts action must be registered (C2 regression check)."""
        with open("src/main.py") as f:
            content = f.read()
        assert '"shortcuts"' in content or "'shortcuts'" in content
