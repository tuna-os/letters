application_id = 'net.codelogistics.letters'

scalable_dir = 'hicolor' / 'scalable' / 'apps'
install_data(
  scalable_dir / ('@0@.svg').format(application_id),
  install_dir: get_option('datadir') / 'icons' / scalable_dir
)

icon_dir = 'hicolor' / 'symbolic' / 'apps'
install_data(
  icon_dir / ('@0@-symbolic.svg').format(application_id),
  install_dir: get_option('datadir') / 'icons' / icon_dir
)

scalable_actions_dir = 'hicolor' / 'scalable' / 'actions'

symbolic_icons = [
  'system-search',
  'text-bold',
  'text-italic',
  'text-underline',
  'insert-list',
  'chain-link',
  'image-round'
]

foreach icon : symbolic_icons
  install_data(
    scalable_actions_dir / ('@0@-symbolic.svg').format(icon),
    install_dir: get_option('datadir') / 'icons' / scalable_actions_dir
  )
endforeach
