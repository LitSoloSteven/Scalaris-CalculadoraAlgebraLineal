"""Montaje de escenas de aplicación sin conservar figuras de capturas anteriores."""
import logging

from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.versionado_recursos import versionar_html
from .figura_aplicacion_transformacion import preparar_escenas_aplicacion

registro = logging.getLogger(__name__)
_URL_TEMA = versionar_html('src="/assets/js/tema_graficos.js"').split('"')[1]
_SINCRONIZAR_TEMA = (
    f'async () => {{ await import("{_URL_TEMA}"); '
    'window.scalaris.sincronizarTemaPlotly(); }'
)


def renderizar_grafica_aplicacion(resultado: dict, tipo_objeto: str) -> None:
    """Añade las escenas al contenedor actual y conserva las coordenadas si fallan."""
    region = ui.column().classes("w-full min-w-0")
    try:
        presentacion = preparar_escenas_aplicacion(resultado, tipo_objeto)
        with region:
            _montar_presentacion(presentacion, tipo_objeto)
    except Exception:
        registro.exception("No se pudo montar la gráfica de la transformación")
        region.clear()
        with region:
            ui.label(textos.GRAFICA_ERROR).classes("texto-secundario text-sm").props('role="status"')


def _montar_presentacion(presentacion: dict, tipo_objeto: str) -> None:
    with ui.column().classes("w-full min-w-0 gap-2"):
        ui.label(textos.GRAFICA_TITULO).classes("texto-principal font-bold")
        ui.label(presentacion["mensaje"]).classes("texto-secundario text-sm")
        if not presentacion["escenas"]:
            return
        ui.label(textos.GRAFICA_ESTILOS).classes("texto-secundario text-sm")
        if tipo_objeto == "vector":
            ui.label(textos.GRAFICA_SEGMENTOS).classes("texto-secundario text-sm")
        for escena in presentacion["escenas"]:
            _montar_escena(escena)


def _montar_escena(escena: dict) -> None:
    ui.label(escena["titulo"]).classes("texto-principal font-semibold")
    ejes = textos.GRAFICA_EJES_3D if escena["figura"].data[0].type == "scatter3d" else textos.GRAFICA_EJES_2D
    ui.label(ejes).classes("texto-secundario text-sm")
    opciones = escena["figura"].to_plotly_json()
    opciones["config"] = dict(displayModeBar=False, scrollZoom=False, doubleClick="reset", responsive=True)
    with ui.element("div").classes("w-full min-w-0").props('role="group"') as region:
        region.props["aria-label"] = escena["titulo"]
        grafica = ui.plotly(opciones).classes("w-full h-80 min-w-0")
        grafica.props.update({"role": "img", "aria-label": textos.GRAFICA_DESCRIPCION})
        grafica.on("plotly_afterplot", js_handler=_SINCRONIZAR_TEMA)
