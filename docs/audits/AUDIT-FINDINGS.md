# GNOME Standards Audit — Letters

Audit date: 2026-06-21
Version: 0.2.0 (forked to https://github.com/hanthor/letters)

---

## 🔴 Critical Issues

### C1. Flatpak source path is local (`file:///home/satvikp/Projects`)
**File:** `org.tunaos.letters.json` line 166
**Problem:** The Letters module source points to a local filesystem path on the developer's machine. This means the Flatpak manifest cannot build for anyone else.
**Fix:** Replace with the actual remote URL (Codeberg or GitHub).

### C2. `app.shortcuts` action referenced but never registered
**File:** `src/window.blp` lines 122, `src/shortcuts-dialog.blp` line 9
**Problem:** The primary menu has a "Keyboard Shortcuts" item and the shortcuts dialog exists (compiled from Blueprint), but no `app.shortcuts` action is created in `main.py`. Clicking this menu item will produce a GTK warning and do nothing.
**Fix:** Register an `app.shortcuts` action in `LettersApplication.__init__()`.

### C3. Icon name marked translatable via `_()`
**File:** `src/window.blp` line 65
```blueprint
icon-name: _("document-new-symbolic");
```
**Problem:** `_()` marks the string for translation, but icon names **must not** be translated — they are looked up in the icon theme by exact name. This will break on non-English locales.
**Fix:** Remove the `_()` wrapper.

---

## 🟠 High Priority

### H1. Developer ID is placeholder
**File:** `data/org.tunaos.letters.metainfo.xml.in`
```xml
<developer id="tld.vendor">
```
**Problem:** `tld.vendor` is a placeholder. Should be `org.tunaos` to match the app ID.
**Fix:** Change to `<developer id="org.tunaos">`.

### H2. Desktop Categories are non-standard
**File:** `data/org.tunaos.letters.desktop.in`
```
Categories=X-Accessories;X-Office;
```
**Problem:** `X-Accessories` and `X-Office` are legacy/unofficial categories. A word processor should use standard Freedesktop categories.
**Fix:** Change to `Categories=Office;WordProcessor;`.

### H3. Desktop Keywords include `GTK` — not useful
**File:** `data/org.tunaos.letters.desktop.in`
```
Keywords=GTK;
```
**Fix:** Use meaningful keywords: `Keywords=word;processor;document;editor;text;pandoc;`.

### H4. GSettings schema is completely empty
**File:** `data/org.tunaos.letters.gschema.xml`
```xml
<schema id="org.tunaos.letters" path="/net/hanthor/letters/">
</schema>
```
**Fix:** Add keys for font, editor width, zoom level, autosave interval, etc.

### H5. Preferences action is a no-op
**File:** `src/main.py` `on_preferences_action` just `print()`s.
**Fix:** Wire up a real `Adw.PreferencesWindow`.

### H6. No `--filesystem` access for fonts or documents
**File:** `org.tunaos.letters.json` finish-args
**Problem:** The sandbox doesn't grant access to the user's fonts or document directories. Loading/saving files will be limited to portals. Font detection relies on system fonts only.
**Fix:** Add appropriate `--filesystem=host` or portal-based access.

---

## 🟡 Medium Priority

### M1. Release metadata is outdated
**File:** `data/org.tunaos.letters.metainfo.xml.in`
**Problem:** Only two release entries (0.1.0, 0.2.0) with dates in 2025. No entry for current build.
**Fix:** Add current release tag entry.

### M2. Missing metainfo URLs
**File:** `data/org.tunaos.letters.metainfo.xml.in`
**Problem:** Missing `<url type="help">`, `<url type="donation">`, `<url type="translate">`. All are commented out.
**Fix:** Add URLs where applicable, remove unused comment boilerplate.

### M3. No Adw.Toast for error/user feedback
**File:** `src/window.py` throughout
**Problem:** All errors use bare `print()` which goes to stderr — invisible to the user. Should use `Adw.Toast` or `Adw.AlertDialog` for user-facing errors.
**Fix:** Replace key error paths with toasts or dialogs.

### M4. No loading/activity indicator
**File:** `src/window.py`
**Problem:** Pandoc conversions (opening/saving large documents) can take seconds with no visual feedback. The window appears frozen.
**Fix:** Set cursor to busy (`Gdk.Cursor`), or use an overlay spinner.

### M5. No spellcheck
**Problem:** WebKitGTK supports spellcheck natively but it's not configured (`webkit.get_spell_checking_enabled()` or similar settings).
**Fix:** Enable WebKit spellcheck.

### M6. `translator-credits` needs real content
**File:** `src/main.py` `on_about_action`
**Fix:** The translators already filled in their credits in `.po` files — verify they render correctly in the About dialog.

---

## 🟢 Low Priority

### L1. Comments about `execCommand` deprecation
**File:** `src/editor.js`
**Note:** Already documented by the author. Should be addressed separately (tracked in execCommand mitigation task).

### L2. Temp files not cleaned up
**File:** `src/window.py` `new_webview`
**Problem:** `NamedTemporaryFile` objects are created but may not be reliably cleaned up if exceptions occur.
**Fix:** Use a context manager (`with tempfile.NamedTemporaryFile() as f:`) or explicit cleanup in finally blocks.

### L3. MIME type metadata in Flatpak
**File:** `org.tunaos.letters.json`
```
--metadata=X-Flatpak-MimeType=text/plain;application/json;image/png;
```
**Problem:** Missing MIME types for DOCX, ODT, MD. These are set in the desktop file but not in Flatpak metadata — may affect file association in some file managers.
**Fix:** Add `application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/vnd.oasis.opendocument.text;text/markdown`.

### L4. No responsive breakpoints
**File:** `src/window.blp`
**Problem:** No `Adw.Breakpoint` for narrow windows. The toolbar may overflow on small screens.
**Fix:** Consider adding a mobile/compact layout breakpoint.

### L5. License file in repo
**Note:** `COPYING` contains GPL-3.0 — correct, but renaming to `COPYING.md` or `LICENSE.md` is more conventional.

---

## Summary Table

| Severity | Count | Task to Address |
|----------|-------|----------------|
| 🔴 Critical | 3 | Fixed in Flatpak manifest, main.py action registration, window.blp |
| 🟠 High | 5 | Addressed across deps, GSettings, desktop/metainfo fixes |
| 🟡 Medium | 6 | Handled in error-handling & code quality task |
| 🟢 Low | 5 | Handled in execCommand mitigation & polish pass |
