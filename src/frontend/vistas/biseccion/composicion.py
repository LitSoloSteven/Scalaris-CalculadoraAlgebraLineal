"""Orden de lectura y montaje de los paneles de bisección."""
from nicegui import ui

from .acciones_captura import construir_acciones, construir_limite, desplegable
from .captura import construir_boton_calculo, construir_captura, construir_intervalo
from .exploracion import PanelExploracion
from .modos_captura import MODO_BUSQUEDA, MODO_INTERVALO, construir_modos, region_modo
from .resolucion_multiple import PanelResolucionMultiple
from .vista_previa import PanelVistaPrevia


def componer_herramienta(vista) -> None:
    """Monta la captura primero y conserva la vista previa a su derecha en escritorio."""
    vista.vista_previa = PanelVistaPrevia(vista)
    vista.exploracion = PanelExploracion(vista)
    vista.resolucion_multiple = PanelResolucionMultiple(vista)
    with ui.column().classes("biseccion-vista vista-raiz w-full mx-auto p-4 gap-5"):
        with ui.element("h1").classes("text-2xl font-bold texto-principal"):
            ui.label("Método de bisección")
        with ui.element("div").classes("biseccion-disposicion w-full"):
            _componer_captura(vista)
            vista.vista_previa.construir()
        with ui.column().classes("w-full min-w-0 gap-5").bind_visibility_from(
                vista.modos, "value", backward=lambda modo: modo == MODO_INTERVALO):
            vista.estado = ui.label("Ingresa una función o carga un ejemplo para comenzar.").classes(
                "texto-secundario").props("role=status aria-live=polite")
            vista.contenedor_resultados = ui.column().classes("w-full min-w-0 gap-5")


def _componer_captura(vista) -> None:
    with ui.column().classes("panel-tarjeta biseccion-captura w-full gap-4 p-6"):
        construir_captura(vista)
        construir_modos(vista)
        vista.region_intervalo = region_modo(vista, MODO_INTERVALO)
        with vista.region_intervalo:
            construir_intervalo(vista)
            with desplegable("Avanzado"):
                construir_limite(vista)
                vista.vista_previa.construir_controles()
            construir_boton_calculo(vista)
        vista.region_busqueda = region_modo(vista, MODO_BUSQUEDA)
        with vista.region_busqueda:
            vista.exploracion.construir()
            vista.resolucion_multiple.construir()
        construir_acciones(vista)
        vista.recientes = ui.row().classes("w-full gap-2")
