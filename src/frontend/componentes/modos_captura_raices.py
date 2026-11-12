"""Selector y regiones de las tareas de captura de una raíz."""
from nicegui import ui

from src.frontend.componentes.selector_opciones import SelectorOpciones

MODO_INTERVALO = "intervalo"
MODO_BUSQUEDA = "busqueda"
_OPCIONES = (
    (MODO_INTERVALO, "Tengo el intervalo", "Tengo el intervalo"),
    (MODO_BUSQUEDA, "Buscar intervalo", "Buscar intervalo"),
)


def construir_modos(vista, nombre_grupo: str) -> None:
    """Construye el selector accesible, con intervalo manual como tarea inicial."""
    vista.modos = SelectorOpciones(_OPCIONES, MODO_INTERVALO, vista.cambiar_modo, nombre_grupo)


def region_modo(vista, modo: str):
    """Asocia una región nombrada que queda fuera del foco al ocultarse."""
    return vista.modos.asociar_contenido(modo, ui.column().classes("w-full gap-4"))
