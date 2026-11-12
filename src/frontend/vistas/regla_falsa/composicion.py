"""Orden de lectura y disposición adaptable de captura y resultados."""
from nicegui import ui
from src.frontend.componentes.previa_expresion_raices import PreviaExpresion

from src.frontend.vistas.biseccion.captura import GUIA_CONTINUIDAD
from .acciones_captura import construir_acciones, mostrar_recientes
from .captura import construir_captura
from .exploracion import PanelExploracion
from .resolucion_multiple import PanelResolucionMultiple
from .modos_captura import MODO_BUSQUEDA, region_modo
from .vista_previa import PanelVistaPrevia
from .seleccion_grafico import SeleccionGrafico
from .continuidad_intervalo import PanelContinuidad
from .estados_entrada import EstadosEntrada


def componer_herramienta(vista) -> None:
    """Monta captura, estado vivo y resultado con los controles y temas de Scalaris."""
    with ui.column().classes("regla-falsa-vista vista-raiz w-full mx-auto p-4 gap-5"):
        with ui.element("h1").classes("text-2xl font-bold texto-principal"):
            ui.label("Método de regla falsa")
        ui.label(GUIA_CONTINUIDAD).classes("text-sm texto-secundario")
        with ui.element("div").classes("disposicion-dividida"):
            with ui.column().classes("disposicion-panel panel-tarjeta p-6 gap-4"):
                _montar_captura(vista)
                vista.contenedor_acciones = ui.column().classes("w-full gap-3")
                vista.recientes = ui.column().classes("w-full gap-2")
            with ui.column().classes("disposicion-panel panel-tarjeta p-6 gap-4"):
                _montar_resultados(vista)
        vista.contenedor_detalle = ui.column().classes("w-full gap-4 min-w-0")
        vista.vista_previa = PanelVistaPrevia(vista)
        vista.vista_previa.construir()
        vista.seleccion_grafico = SeleccionGrafico(vista)
        vista.seleccion_grafico.construir()
        with vista.contenedor_acciones:
            construir_acciones(vista)
        mostrar_recientes(vista)


def _montar_captura(vista) -> None:
    construir_captura(vista)
    vista.estados_entrada = EstadosEntrada(vista)
    vista.estados_entrada.construir()
    vista.continuidad = PanelContinuidad(vista)
    vista.continuidad.construir()
    vista.previa_expresion = PreviaExpresion()
    with region_modo(vista, MODO_BUSQUEDA):
        vista.exploracion = PanelExploracion(vista)
        vista.exploracion.construir()
        vista.resolucion_multiple = PanelResolucionMultiple(vista)
        vista.resolucion_multiple.construir()


def _montar_resultados(vista) -> None:
    with ui.element("h2").classes("text-lg font-semibold texto-principal"):
        ui.label("Resultado")
    vista.estado = ui.label("Ingresa una función y sus extremos, busca un intervalo o carga un ejemplo.").classes(
        "texto-secundario").props("role=status aria-live=polite aria-atomic=true tabindex=-1")
    vista.contenedor_resultados = ui.column().classes("w-full gap-4")
