"""Selector de tarea y regiones persistentes de bisección."""
from src.frontend.componentes.modos_captura_raices import (
    MODO_BUSQUEDA, MODO_INTERVALO, construir_modos as construir_modos_compartidos, region_modo,
)


def construir_modos(vista) -> None:
    """Monta el conmutador accesible conservando los controles de ambas tareas."""
    construir_modos_compartidos(vista, "Tarea de bisección")
    vista.modos.classes("biseccion-modos").props("data-selector-movimiento-local")
    vista.modos.on("click.capture", js_handler="evento => window.scalaris.movimientoBiseccion.seleccionarModo(evento)")
