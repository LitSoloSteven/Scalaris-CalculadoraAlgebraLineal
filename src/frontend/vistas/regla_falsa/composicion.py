"""Orden de lectura y disposición adaptable de captura y resultados."""
from nicegui import ui

from src.frontend.vistas.biseccion.captura import GUIA_CONTINUIDAD
from .acciones_captura import construir_acciones, mostrar_recientes
from .captura import construir_captura


def componer_herramienta(vista) -> None:
    """Monta captura, estado vivo y resultado con los controles y temas de Scalaris."""
    with ui.column().classes("regla-falsa-vista vista-raiz w-full mx-auto p-4 gap-5"):
        with ui.element("h1").classes("text-2xl font-bold texto-principal"):
            ui.label("Método de regla falsa")
        ui.label(GUIA_CONTINUIDAD).classes("text-sm texto-secundario")
        with ui.element("div").classes("disposicion-dividida"):
            with ui.column().classes("disposicion-panel panel-tarjeta p-6 gap-4"):
                construir_captura(vista)
                vista.contenedor_acciones = ui.column().classes("w-full gap-3")
                vista.recientes = ui.column().classes("w-full gap-2")
            with ui.column().classes("disposicion-panel panel-tarjeta p-6 gap-4"):
                _montar_resultados(vista)
        with vista.contenedor_acciones:
            construir_acciones(vista)
        mostrar_recientes(vista)


def _montar_resultados(vista) -> None:
    with ui.element("h2").classes("text-lg font-semibold texto-principal"):
        ui.label("Resultado")
    vista.estado = ui.label("Ingresa una función y sus extremos o carga un ejemplo.").classes(
        "texto-secundario").props("role=status aria-live=polite aria-atomic=true")
    vista.contenedor_resultados = ui.column().classes("w-full gap-4")
