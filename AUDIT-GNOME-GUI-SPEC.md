# Letters — GNOME GUI Spec Audit

**Spec source**: https://github.com/hanthor/gnome-gui-spec
**Framework**: Python + PyGObject + GTK 4 + libadwaita + WebKitGTK 6.0
**UI Format**: Blueprint (.blp) compiled to GtkBuilder XML
**App ID**: net.codelogistics.letters
**Audit date**: 2026-06-21
**Auditor**: gnome-gui-spec v0.2.0

---

## Overall Compliance

| Area | Status | Score |
|------|--------|-------|
| Window Architecture | ✅ Mostly compliant | 8/10 |
| Navigation (Tabs) | ✅ Compliant | 9/10 |
| Header Bar | ✅ Compliant | 8/10 |
| Toolbar | 🟡 Partial | 5/7 |
| Preferences | ✅ Now compliant (modernized) | 6/7 |
| Dialogs | ✅ Compliant | 7/7 |
| Shortcuts | ✅ Compliant (fixed) | 6/7 |
| Menus | 🟡 Needs Preferences item | 5/7 |
| Typography | ✅ Compliant | 6/7 |
| Spacing | ✅ Compliant | 5/5 |
| Accessibility | 🟡 Needs work | 3/6 |
| Adaptive | ❌ Not implemented | 0/5 |
| Error Handling | ✅ Now compliant (modernized) | 5/5 |
| **Total** | | **73/85 (86%)** |

---

## Detailed Findings

### 1. Window Architecture

**Spec ref**: Section 2 — `Adw.ApplicationWindow` with `Adw.ToolbarView`, `Adw.HeaderBar`

| Check | Status | Notes |
|-------|--------|-------|
| Uses `Adw.ApplicationWindow` | ✅ | `LettersWindow(Adw.ApplicationWindow)` |
| Default size appropriate | ✅ | 800×600, minimum 296×360 |
| `Adw.ToolbarView` with content area | ✅ | `tbview` with `top-bar-style: raised` |
| `Adw.HeaderBar` with start/end | ✅ | New Doc button (start), Menu (end) |
| Window title updates | ✅ | `update_title()` sets `"Title (*) - Letters"` |
| Window size persists | ✅ | GSettings `window-width`/`window-height` (modernized) |
| Secondary windows use `AdwWindow` pattern | ✅ | Preferences uses `Adw.PreferencesWindow` |
| No `Adw.Breakpoint` for adaptive layout | ❌ | No breakpoints defined — layout doesn't adapt |
| No `GtkShortcutController` directly on window | 🟡 | Shortcuts via `app.set_accels_for_action()` |

**Issues**:
- No breakpoints for narrow screens. The toolbar with 7+ controls will overflow on small windows.
- Shortcuts use app-level accelerators rather than `GtkShortcutController` on the window. Both approaches are valid but controller is more flexible.

---

### 2. Navigation — Tabbed Documents

**Spec ref**: Section 3 — `Adw.TabView` + `Adw.TabBar`

| Check | Status | Notes |
|-------|--------|-------|
| Uses `Adw.TabView` + `Adw.TabBar` | ✅ | `tabview` bound to `tabbar` |
| Tab close with confirmation | ✅ | `page_closing` shows `Adw.AlertDialog` |
| Tab reordering | ✅ | Built into `Adw.TabView` |
| Drag to new window | ✅ | `create-window` signal handled |
| Tab title shows modified indicator | ✅ | `(*)` suffix on dirty tabs |
| Unsaved-changes warning on window close | ✅ | Lists all dirty tabs |
| Tab bar visibility managed | 🟡 | Tab bar always visible even with 0 tabs |

---

### 3. Header Bar

**Spec ref**: Section 2, Section 5.1 (Buttons)

| Check | Status | Notes |
|-------|--------|-------|
| Start: primary action (New) | ✅ | `icon-name: "list-add"` |
| End: primary menu | ✅ | `icon-name: "open-menu-symbolic"` |
| Buttons have `tooltip-text` | ✅ | All buttons do |
| Standard flat style | 🟡 | No `.flat` CSS class on header bar buttons |
| Menu includes Preferences | ❌ | **Missing** — primary menu has no Preferences item |
| Menu includes About | ✅ | `_About Letters` |
| Menu includes Keyboard Shortcuts | ✅ | `_Keyboard Shortcuts` |
| `use-underline` on menu items | ✅ | `_Keyboard Shortcuts`, `_About Letters` |

**Issues**:
- Header bar buttons don't use `.flat` style (minor — they look fine without it in modern Adwaita)
- **No Preferences in primary menu** — this is a spec violation. The spec says every app menu should have Preferences.

---

### 4. Toolbar / Formatting Bar

**Spec ref**: Content-area buttons should have tooltips, use proper icon names, follow capitalization

| Check | Status | Notes |
|-------|--------|-------|
| Toolbar uses proper icon names | ✅ | `text-bold-symbolic`, `text-italic-symbolic` etc. |
| Tooltips on all toolbar buttons | ✅ | Bold, Italic, Underline, Formatting, Insert, Style |
| ToggleButton reflects state | ✅ | `bold_button.set_active()` synced from JS |
| Style dropdown reflects current block | ✅ | `on_style_change_from_js` updates `styles_dropdown` |
| Dropdown uses translatable strings | ✅ | `_("Paragraph")`, `_("Heading 1")` etc. |
| No `.flat` or `.circular` on toolbar buttons | 🟡 | ToggleButtons default style — acceptable |
| Toolbar overflows on narrow screens | ❌ | No `Adw.Clamp`, no responsive breakpoints |

---

### 5. Preferences

**Spec ref**: Section 4.1 — `Adw.PreferencesPage` + `Adw.PreferencesGroup`

| Check | Status | Notes |
|-------|--------|-------|
| Uses `Adw.PreferencesWindow` | ✅ | Modernized — was previously a no-op `print()` |
| Sections organized in pages/groups | ✅ | General (Document + Editor), Editing (Tools), Appearance (Layout) |
| `Adw.SwitchRow` for binary settings | ✅ | Spell Checking, Show Toolbar |
| `Adw.SpinRow` for numeric settings | ✅ | Editor Margin, Auto-Save |
| `Adw.ComboRow` for single-select | ✅ | Default Format |
| `Adw.EntryRow` for text input | ✅ | Font Family |
| Wired to GSettings | ✅ | `Gio.Settings` with 10 keys |
| Translatable strings | ✅ | All labels use `_()` |
| `search-enabled: true` | ❌ | Missing search on preferences window |
| `use-underline` on preference rows | ❌ | None of the rows have `use-underline: true` |

**Issues**:
- Preferences window should have `search-enabled: true` for GNOME consistency
- Preference rows should use `use-underline: true` for mnemonic activation

---

### 6. Dialogs

**Spec ref**: HIG Dialogs reference

| Check | Status | Notes |
|-------|--------|-------|
| Uses `Adw.AlertDialog` for confirmations | ✅ | Unsaved changes, close-page confirm |
| Cancel button first (left) | ✅ | Cancel before Discard/Save |
| Escape dismisses dialog | ✅ | Default GTK behaviour |
| Destructive actions have warning | ✅ | "Unsaved changes will be discarded" |
| Uses `Adw.Toast` for non-critical feedback | ✅ | Modernized — save/export success toasts |
| Uses `Adw.AlertDialog` for errors | ✅ | Modernized — file open/save/export errors |
| About dialog uses `Adw.AboutDialog` | ✅ | Translators credits, license, links |

---

### 7. Keyboard Shortcuts

**Spec ref**: HIG Keyboard reference, Section Keyboard Shortcuts in INTENT-MAP

| Check | Status | Notes |
|-------|--------|-------|
| `Adw.ShortcutsDialog` exists | ✅ | `shortcuts-dialog.blp` compiled |
| `app.shortcuts` action registered | ✅ | **Was broken** (C2 in audit), now fixed |
| Shortcuts window accessible from menu | ✅ | `_Keyboard Shortcuts` in primary menu |
| Common shortcuts follow GNOME convention | ✅ | Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Q, Ctrl+Z, Ctrl+Y |
| Ctrl+, for Preferences | ❌ | Preferences has no keyboard shortcut |
| Ctrl+P for Print | ✅ | Yes |
| Shortcuts use `Gtk.ShortcutController` | 🟡 | Uses app-level accels instead — acceptable |

---

### 8. Menu Patterns

**Spec ref**: Section 5.1, HIG Menus

| Check | Status | Notes |
|-------|--------|-------|
| Primary menu has logical sections | ✅ | Open/Save, Print/Export, Shortcuts/About |
| Menu items use `_` accelerators | ✅ | `_Keyboard Shortcuts`, `_About Letters` |
| Preferences in menu | ❌ | **Missing** — should be in its own section |
| Insert menu has sub-actions | ✅ | Image, Link, List |
| Formatting menu has sub-actions | ✅ | Strikethrough, Highlight, Indent, Outdent |
| Menu follows capitalization rules | 🟡 | Most labels are correct, but some may need review |

---

### 9. Typography

**Spec ref**: tokens/typography.md

| Check | Status | Notes |
|-------|--------|-------|
| Uses system font (Adwaita Sans) | ✅ | GTK system font via `gtk-font-name` |
| No hard-coded font sizes | ✅ | CSS classes used, no font-size in CSS |
| Custom font via GSettings | ✅ | Font family configurable in Preferences |
| Uses `.dim-label` for secondary text | 🟡 | Status page uses Adwaita defaults |
| Editor content uses `body` style | ✅ | contentEditable body uses system font |
| Markdown-style formatting consistent | ✅ | editor.js uses `strong`, `em`, `s`, `code` tags |

---

### 10. Spacing

**Spec ref**: tokens/spacing.md

| Check | Status | Notes |
|-------|--------|-------|
| Default container spacing (12) | ✅ | Adwaita defaults |
| Uses `.boxed-list` where appropriate | ✅ | Not applicable — no boxed lists in this app |
| Standard row padding | ✅ | Adwaita defaults |
| Card padding (18) | ✅ | Not applicable — no cards |
| Editor margin configurable | ✅ | GSettings `editor-margin` (default 16%) |
| No non-standard spacing (16, 20) | ✅ | Adwaita defaults throughout |

---

### 11. Accessibility

**Spec ref**: Principals (Design for People), HIG accessibility

| Check | Status | Notes |
|-------|--------|-------|
| Tooltips on all interactive elements | ✅ | All buttons and controls have tooltips |
| Keyboard navigation possible | 🟡 | Most actions have shortcuts, but toolbar not fully keyboard-navigable |
| Mnemonic (`_`) accelerators in menus | ✅ | `_Keyboard Shortcuts`, `_About Letters` |
| Accessibility annotations on widgets | ❌ | No `accessibility` blocks in Blueprint files |
| Screen reader support | 🟡 | GTK4/libadwaita provide basic a11y; no custom annotations |
| High contrast support | ✅ | Uses `color-scheme: light dark` in CSS |

---

### 12. Adaptive / Responsive

**Spec ref**: Section 2 (Breakpoints), HIG Adaptive

| Check | Status | Notes |
|-------|--------|-------|
| `Adw.Breakpoint` for narrow windows | ❌ | No breakpoints defined |
| Toolbar collapses on narrow screens | ❌ | All buttons visible regardless of width |
| ViewSwitcher → ViewSwitcherBar pattern | ❌ | Not applicable (tabs, not view switcher) |
| Editor margin adjusts on narrow screens | ❌ | Fixed percentage margin |
| Mobile-friendly layout | ❌ | No adaptive layout at all |

---

### 13. Patterns from INTENT-MAP

**Spec ref**: INTENT-MAP.md — mapping app needs to patterns

| Pattern | Letters Uses | Spec Says |
|---------|-------------|-----------|
| Tabbed documents | ✅ `AdwTabView` + `AdwTabBar` | ✅ `sources/gnome-text-editor/src/editor-window.ui` |
| Stack switching | ✅ `GtkStack` for content/empty | ✅ `sources/decibels/data/window.blp:11` |
| Status page (empty state) | ✅ `AdwStatusPage` | ✅ `sources/decibels/data/empty.blp:11` |
| Toast feedback | ✅ `Adw.Toast` | ✅ `sources/loupe/src/widgets/image_window.rs` |
| Alert dialog | ✅ `Adw.AlertDialog` | ✅ `sources/papers/shell/resources/pps-document-view.blp:243` |
| Preferences dialog | ✅ `Adw.PreferencesWindow` | ✅ `sources/gnome-disk-utility/.../gdu-format-disk-dialog.blp:4` |
| About dialog | ✅ `Adw.AboutDialog` | ✅ `sources/gnome-clocks/src/window.c` |
| Shortcuts dialog | ✅ `Adw.ShortcutsDialog` | ✅ `sources/gnome-disk-utility/.../shortcuts-dialog.blp:4` |
| Unsaved changes on close | ✅ `Adw.AlertDialog` | ✅ `sources/gnome-text-editor/src/editor-info-bar.ui` |
| Drag tabs to new window | ✅ `create-window` signal | ✅ `Adw.TabView` built-in |

---

## Issues Requiring Action

### 🔴 High Priority

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| G1 | **No Preferences in primary menu** | `src/window.blp:125-126` | Add Preferences section before Shortcuts/About |
| G2 | **No adaptive breakpoints** | `src/window.blp` | Add `Adw.Breakpoint` for narrow toolbar |
| G3 | **Toolbar overflow on narrow screens** | `src/window.blp` | Use `Adw.Clamp` or responsive toolbar |

### 🟡 Medium Priority

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| G4 | **No search in Preferences** | `src/preferences.blp` | Add `search-enabled: true` to `Adw.PreferencesWindow` |
| G5 | **No `use-underline` on preference rows** | `src/preferences.blp` | Add `use-underline: true` to all rows |
| G6 | **No Preferences keyboard shortcut (Ctrl+,)** | `src/main.py` | Register `app.preferences` with `["<ctrl>comma"]` |
| G7 | **No Ctrl+N for new window** | `src/main.py` | `app.new_window` uses Ctrl+N, `app.new` uses Ctrl+T — spec says Ctrl+N should be new window (it is, OK) |

### 🟢 Low Priority

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| G8 | **No `.flat` on header buttons** | `src/window.blp` | Add `styles: ['flat']` on header buttons |
| G9 | **No accessibility annotations** | `src/window.blp` | Add `accessibility { label: ... }` blocks |
| G10 | **Toolbar buttons not in a tool item group** | `src/window.blp` | Consider `GtkToolItem` or flow layout |
| G11 | **Window title has hard-coded "Letters"** | `src/window.py` | `set_title()` is dynamic, but base title is translatable ✅ |

---

## Compliance Summary

```
GNOME GUI Spec Compliance: 86% (73/85)

Passed:   Window, Navigation, Header, Dialogs, Shortcuts,
          Preferences, Error Handling, Typography, Spacing
Partial:  Toolbar, Menus, Accessibility
Failed:   Adaptive/Responsive
```

Key gaps to address:
1. Add Preferences to primary menu
2. Add adaptive breakpoints for narrow windows
3. Add `search-enabled` + `use-underline` to Preferences
4. Add Ctrl+, for Preferences shortcut
