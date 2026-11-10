"""Tareas manual y exploratoria con regiones persistentes y accesibles."""
from nicegui import ui

from src.frontend.componentes.selector_opciones import SelectorOpciones

MODO_INTERVALO = "intervalo"
MODO_BUSQUEDA = "busqueda"
_OPCIONES = (
    (MODO_INTERVALO, "Tengo el intervalo", "Tengo el intervalo"),
    (MODO_BUSQUEDA, "Buscar intervalo", "Buscar intervalo"),
)


def construir_modos(vista) -> None:
    """Monta el selector de tarea con el modo manual como valor inicial."""
    vista.modos = SelectorOpciones(_OPCIONES, MODO_INTERVALO, vista.cambiar_modo, "Tarea de regla falsa")


def region_modo(vista, modo: str):
    """Asocia una región nombrada que queda fuera del foco al ocultarse."""
    return vista.modos.asociar_contenido(modo, ui.column().classes("w-full gap-4"))
