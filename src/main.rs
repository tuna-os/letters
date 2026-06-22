// main.rs — Letters word processor, pure Rust + gtk4-rs.
// SPDX-License-Identifier: GPL-3.0-or-later

use gtk4 as gtk;
use gtk::prelude::*;

mod window;
mod engine;
mod export;

fn main() {
    let app = libadwaita::Application::new(Some("org.tunaos.letters"));
    app.connect_activate(|app| {
        let win = window::LettersWindow::new(app);
        win.present();
    });
    app.run();
}
