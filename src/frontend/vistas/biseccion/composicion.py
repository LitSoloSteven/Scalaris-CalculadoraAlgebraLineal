"""Orden de lectura y montaje de los paneles de bisección."""
from nicegui import ui

from .acciones_captura import construir_acciones, construir_limite, desplegable
from .captura import construir_boton_calculo, construir_captura, construir_intervalo
from .continuidad_intervalo import PanelContinuidad
from .exploracion import PanelExploracion
from .modos_captura import MODO_BUSQUEDA, MODO_INTERVALO, construir_modos, region_modo
from .previa_expresion import PreviaExpresion
from .resolucion_multiple import PanelResolucionMultiple
from .seleccion_grafico import SeleccionGrafico
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
            vista.seleccion_grafico.enlazar(vista.vista_previa.grafica)
        with ui.column().classes("w-full min-w-0 gap-5").bind_visibility_from(
                vista.modos, "value", backward=lambda modo: modo == MODO_INTERVALO):
            vista.estado = ui.label("Ingresa una función o carga un ejemplo para comenzar.").classes(
                "texto-secundario").props("role=status aria-live=polite")
            vista.contenedor_resultados = ui.column().classes("w-full min-w-0 gap-5")


def _componer_captura(vista) -> None:
    with ui.column().classes("panel-tarjeta biseccion-captura w-full gap-4 p-6"):
        construir_captura(vista)
        vista.previa_expresion = PreviaExpresion()
        construir_modos(vista)
        with ui.element("div").classes("biseccion-regiones w-full"):
            _componer_regiones(vista)
        construir_acciones(vista)
        vista.recientes = ui.row().classes("w-full gap-2")


def _componer_regiones(vista) -> None:
    with region_modo(vista, MODO_INTERVALO) as vista.region_intervalo:
        construir_intervalo(vista)
        with desplegable("Avanzado"):
            construir_limite(vista)
            vista.vista_previa.construir_controles()
        construir_boton_calculo(vista)
        vista.continuidad = PanelContinuidad(vista)
        vista.continuidad.construir()
    with region_modo(vista, MODO_BUSQUEDA) as vista.region_busqueda:
        vista.exploracion.construir()
        vista.seleccion_grafico = SeleccionGrafico(vista)
        vista.seleccion_grafico.construir()
        vista.resolucion_multiple.construir()
