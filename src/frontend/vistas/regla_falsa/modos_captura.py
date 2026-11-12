"""Tareas manual y exploratoria con regiones persistentes y accesibles."""
from src.frontend.componentes.modos_captura_raices import (
    MODO_BUSQUEDA, MODO_INTERVALO, construir_modos as construir_modos_compartidos, region_modo,
)


def construir_modos(vista) -> None:
    """Monta el selector de tarea con el modo manual como valor inicial."""
    construir_modos_compartidos(vista, "Tarea de regla falsa")
