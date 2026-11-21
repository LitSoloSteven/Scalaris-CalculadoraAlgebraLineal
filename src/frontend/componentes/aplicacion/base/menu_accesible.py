"""Estado expandido compartido entre activadores de menús."""


def vincular_estado_menu(boton, menu) -> None:
    """Sincroniza aria-expanded al abrir y cerrar el menú asociado al botón."""
    boton.props('aria-haspopup="menu" aria-expanded="false"')
    menu.on("show", lambda _: boton.props('aria-expanded="true"'))
    menu.on("hide", lambda _: boton.props('aria-expanded="false"'))
