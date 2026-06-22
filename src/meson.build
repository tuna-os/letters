pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'letters'
gnome = import('gnome')

# Shared scaffold — consumed as a meson subproject, installed next to the
# app package so both import from pkgdatadir (which the launcher puts on sys.path).
suite_common = subproject('suite-common')
sc_sources = suite_common.get_variable('suite_common_sources')
install_data(sc_sources, install_dir: pkgdatadir / 'suite_common')

blueprints = custom_target('blueprints',
  input: files(
    'window.blp',
    'shortcuts-dialog.blp',
    'preferences.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)


gnome.compile_resources('letters',
  'letters.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'letters.in',
  output: 'letters',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

letters_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'preferences.py',
  'editor.js',
  'styles.css'
]

install_data(letters_sources, install_dir: moduledir)
