"""Disposición de la captura, la gráfica y la solución de raíces."""
from collections.abc import Callable
from dataclasses import dataclass
import html

from nicegui import ui
from nicegui.elements.column import Column

_CLASE_CONTENEDOR = "metodos-raices-vista vista-raiz disposicion-herramienta w-full max-w-6xl mx-auto p-4 gap-5"


@dataclass(frozen=True)
class RegionesSolucionRaices:
    """Contiene las regiones para el resumen y la tabla, y para el procedimiento."""

    resultados: Column
    procedimiento: Column


def montar_estructura_metodos_raices(
    titulo: str,
    descripcion: str,
    montar_captura: Callable[[], None],
    montar_grafica: Callable[[], None],
    montar_auxiliar_resultados: Callable[[], None] | None = None,
) -> RegionesSolucionRaices:
    """Muestra el encabezado, monta captura y gráfica arriba, y devuelve las regiones de salida abajo."""
    with ui.column().classes(_CLASE_CONTENEDOR):
        with ui.column().classes("metodos-raices-encabezado"):
            ui.html(html.escape(titulo), tag="h1").classes("text-2xl font-bold texto-principal m-0")
            ui.label(descripcion).classes("text-sm texto-secundario")
        with ui.element("div").classes("disposicion-captura-fila metodos-raices-fila-captura"):
            with ui.card().classes("metodos-raices-captura panel-tarjeta w-full"):
                montar_captura()
            with ui.card().classes("metodos-raices-previa panel-tarjeta w-full min-w-0"):
                montar_grafica()
        with ui.column().classes("disposicion-resultados w-full min-w-0 gap-4"):
            if montar_auxiliar_resultados is not None:
                montar_auxiliar_resultados()
            resultados = ui.column().classes("metodos-raices-resultados w-full min-w-0")
            procedimiento = ui.column().classes("w-full min-w-0")

    return RegionesSolucionRaices(resultados, procedimiento)
