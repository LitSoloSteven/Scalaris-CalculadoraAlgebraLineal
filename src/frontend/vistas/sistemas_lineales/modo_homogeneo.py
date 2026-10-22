"""Activacion de captura Ax=0 conservando los terminos de la captura general."""


def cambiar_modo_homogeneo(vista, activo: bool) -> None:
    """Fija b=0 sin pedir su captura y restaura b al salir del modo, retirando resultados previos."""
    vista.restablecer_resultados()
    vista.cuadricula.establecer_modo_homogeneo(activo)
