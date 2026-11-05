"""Selector de tarea y regiones persistentes de bisección."""
from nicegui import ui

from src.frontend.componentes.selector_opciones import SelectorOpciones

MODO_INTERVALO = "intervalo"
MODO_BUSQUEDA = "busqueda"
_OPCIONES = (
    (MODO_INTERVALO, "Tengo el intervalo", "Tengo el intervalo"),
    (MODO_BUSQUEDA, "Buscar intervalo", "Buscar intervalo"),
)


def construir_modos(vista) -> None:
    """Monta el conmutador accesible conservando los controles de ambas tareas."""
    vista.modos = SelectorOpciones(_OPCIONES, MODO_INTERVALO, vista.cambiar_modo, "Tarea de bisección")


def region_modo(vista, modo: str):
    """Devuelve la región asociada a la tarea, fuera de foco cuando se oculta."""
    region = ui.column().classes("w-full gap-4")
    return vista.modos.asociar_contenido(modo, region)
