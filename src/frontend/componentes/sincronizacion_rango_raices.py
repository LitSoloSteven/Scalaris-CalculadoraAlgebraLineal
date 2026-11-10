"""Escritura coordinada del rango compartido entre gráfica y exploración."""
from collections.abc import Callable


def sincronizar_rango(vista, valores: tuple, transaccion: Callable) -> None:
    """Escribe límites en ambos paneles e invalida solo sus respuestas visuales."""
    previa, exploracion = vista.vista_previa, vista.exploracion
    with transaccion(vista):
        for panel in (previa, exploracion):
            panel.minimo.set_value(valores[0])
            panel.maximo.set_value(valores[1])
    exploracion.actualizar_paso()
    exploracion.invalidar()
    previa.programar()
