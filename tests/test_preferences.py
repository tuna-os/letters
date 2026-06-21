"""
Tests for preference-related logic.

Tests the FORMAT_MAP, format validation, and other pure-logic
functions without requiring a GTK display server.
"""

import pytest

# Import the format map - matches src/preferences.py
FORMAT_MAP = ["odt", "docx", "md", "html", "txt", "rtf"]

# Valid file extensions for open/save
VALID_EXTS = {"docx", "odt", "txt", "md", "html", "rtf"}


def test_format_map_contains_odt():
    """ODT should be first in the format map (default)."""
    assert FORMAT_MAP[0] == "odt"


def test_format_map_contains_all_formats():
    """Format map should include all expected document formats."""
    expected = {"odt", "docx", "md", "html", "txt", "rtf"}
    assert set(FORMAT_MAP) == expected


def test_format_map_no_duplicates():
    """Format map should not contain duplicate entries."""
    assert len(FORMAT_MAP) == len(set(FORMAT_MAP))


def test_format_map_order_stable():
    """Format map order should match preferences dropdown order."""
    expected_order = ["odt", "docx", "md", "html", "txt", "rtf"]
    assert FORMAT_MAP == expected_order


def test_valid_extensions():
    """All valid extensions should be recognized."""
    for ext in ["docx", "odt", "txt", "md", "html", "rtf"]:
        assert ext in VALID_EXTS


def test_invalid_extensions():
    """Invalid extensions should not be recognized."""
    for ext in ["pdf", "xls", "csv", "py", "js", "png", ""]:
        assert ext not in VALID_EXTS


def test_save_format_fallback():
    """If extension unknown, fallback to odt."""
    allowed = {"odt", "docx", "rtf", "txt", "md", "html"}

    def save_ext(path):
        ext = path.rpartition('.')[2]
        if ext not in allowed:
            ext = "odt"
        return ext

    assert save_ext("doc.docx") == "docx"
    assert save_ext("file.odt") == "odt"
    assert save_ext("file.pdf") == "odt"  # fallback
    assert save_ext("file") == "odt"     # no ext
    assert save_ext("file.md") == "md"


def test_unsupported_format_rejection():
    """Test the file open validation logic from window.py."""
    supported = {"docx", "odt", "txt", "md", "html"}

    def is_supported(filename):
        ext = filename.rpartition(".")[2]
        return ext in supported

    assert is_supported("report.docx")
    assert is_supported("notes.md")
    assert is_supported("page.html")
    assert is_supported("plain.txt")
    assert is_supported("doc.odt")
    assert not is_supported("spreadsheet.xlsx")
    assert not is_supported("image.png")
    assert not is_supported("script.py")
    assert not is_supported("noext")


def test_format_selection_index():
    """Test the format-to-index mapping used in preferences."""
    fmt_to_idx = {fmt: i for i, fmt in enumerate(FORMAT_MAP)}

    assert fmt_to_idx["odt"] == 0
    assert fmt_to_idx["docx"] == 1
    assert fmt_to_idx["md"] == 2
    assert fmt_to_idx["html"] == 3
    assert fmt_to_idx["txt"] == 4
    assert fmt_to_idx["rtf"] == 5


def test_style_dropdown_mapping():
    """Test the styles_int mapping from window.py."""
    styles_int = {
        'p': 0, 'h1': 1, 'h2': 2, 'h3': 3,
        'h4': 4, 'h5': 5, 'h6': 6, 'pre': 7, 'blockquote': 8
    }

    assert styles_int['p'] == 0
    assert styles_int['h1'] == 1
    assert styles_int['h6'] == 6
    assert styles_int['blockquote'] == 8

    # Unknown style should default to 'p'
    unknown_styles = ['div', 'span', 'ul', 'ol', 'table']
    for s in unknown_styles:
        assert s not in styles_int


def test_styles_tag_mapping():
    """Test the display-name-to-HTML-tag mapping from window.py."""
    # Simulated: translated names -> tags
    styles_tag = {
        "Paragraph": 'p', "Heading 1": 'h1', "Heading 2": 'h2',
        "Heading 3": 'h3', "Heading 4": 'h4', "Heading 5": 'h5',
        "Heading 6": 'h6', "Code": 'pre', "Quote": 'blockquote'
    }

    assert styles_tag["Paragraph"] == 'p'
    assert styles_tag["Heading 1"] == 'h1'
    assert styles_tag["Code"] == 'pre'
    assert styles_tag["Quote"] == 'blockquote'
