// export.rs — Typst export for Letters.
pub fn to_typst(text: &str) -> String {
    format!("#set page(width: auto, height: auto)\n{}", text)
}

pub fn to_pdf(text: &str, path: &str) -> Result<(), String> {
    let world = typst::World::new(typst::CompilerFeat::default());
    let doc = typst::compile(text, &world).map_err(|e| format!("{:?}", e))?;
    std::fs::write(path, &doc).map_err(|e| format!("{}", e))
}
