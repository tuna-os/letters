use gtk4::prelude::*;
fn main() {
    let app = gtk4::Application::new(Some("org.tunaos.letters"), Default::default());
    app.connect_activate(|app| {
        let win = gtk4::ApplicationWindow::new(app);
        win.set_title(Some("Letters"));
        win.set_default_size(800, 600);
        let label = gtk4::Label::new(Some("📄 Letters — Rust native"));
        win.set_child(Some(&label));
        win.present();
    });
    app.run();
}
