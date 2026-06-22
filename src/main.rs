// main.rs — Letters word processor, pure Rust + gtk4-rs.
// SPDX-License-Identifier: GPL-3.0-or-later

use gtk4 as gtk;
use gtk::prelude::*;

mod window;

fn main() {
    let app = libadwaita::Application::new(Some("org.tunaos.letters"), Default::default());
    app.connect_activate(|app| {
        let win = window::LettersWindow::new(app);
        win.present();
    });
    app.run();
}
