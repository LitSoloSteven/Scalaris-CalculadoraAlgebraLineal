"""Disposición de la captura, la gráfica y la solución de raíces."""
from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui
from nicegui.elements.column import Column

_CLASE_CONTENEDOR = "metodos-raices-vista vista-raiz w-full max-w-6xl mx-auto p-4 gap-4"


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
) -> RegionesSolucionRaices:
    """Muestra el encabezado, monta la captura y la gráfica, y devuelve las regiones de salida."""
    with ui.column().classes(_CLASE_CONTENEDOR):
        with ui.column().classes("metodos-raices-encabezado"):
            ui.label(titulo).classes("text-2xl font-bold texto-principal")
            ui.label(descripcion).classes("text-sm texto-secundario")
        with ui.card().classes("metodos-raices-captura panel-tarjeta w-full"):
            montar_captura()

    with ui.column().classes(_CLASE_CONTENEDOR):
        with ui.column().classes("metodos-raices-previa w-full min-w-0"):
            montar_grafica()
        resultados = ui.column().classes("metodos-raices-resultados w-full min-w-0")
        procedimiento = ui.column().classes("w-full min-w-0")

    return RegionesSolucionRaices(resultados, procedimiento)
