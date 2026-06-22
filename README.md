# Letters

![Letters logo](data/icons/hicolor/scalable/apps/net.codelogistics.letters.svg)

[![Please do not theme this app](https://stopthemingmy.app/badge.svg)](https://stopthemingmy.app)

### Modern word processor for the GNOME desktop

Letters is a modern, minimalist word processor for the GNOME desktop, with support for reading and writing DOCX, ODT, MD and HTML, using the [pandoc](https://pandoc.org) library.

It can also export your documents to PDF using [weasyprint](https://weasyprint.org/).

> **This is a hard fork** of [Letters by Satvik Patwardhan](https://codeberg.org/eyekay/letters),
> maintained as part of the [TunaOS](https://github.com/tuna-os) GNOME office suite alongside
> [Tables](https://github.com/hanthor/tables) and [Decks](https://github.com/hanthor/decks).
> All credit for the original Letters architecture, design, and implementation goes to
> **Satvik Patwardhan** and contributors.
> 
> This fork extends the original by adopting the [suite-common](https://github.com/hanthor/suite-common)
> shared scaffold, adding keyboard shortcuts, formatting toolbar extensions, find/replace, word count,
> table insertion, and comprehensive test infrastructure.

## Install

[![Get it on Flathub](https://flathub.org/api/badge?locale=en)](https://flathub.org/apps/net.codelogistics.letters/)

Or from the TunaOS Flatpak remote:

```bash
flatpak remote-add tuna-os oci+https://tuna-os.github.io/flatpak-index
flatpak install tuna-os net.codelogistics.letters
```

## Building

```bash
git clone https://github.com/hanthor/letters.git
cd letters
just setup   # clones suite-common subproject
just build   # builds & installs Flatpak
just run     # launches the app
```

## Test

```bash
just lint         # syntax check
pytest tests/     # 81 unit tests
```

## License

GPL-3.0-or-later.

## Credits

**Original author:** [Satvik Patwardhan](https://codeberg.org/eyekay) — the original Letters word processor, its architecture, design, and implementation.

Built with GTK 4, WebKitGTK, libadwaita, pypandoc, blueprint-compiler, weasyprint, and Flatpak.
