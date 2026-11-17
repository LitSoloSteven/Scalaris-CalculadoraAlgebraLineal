"""Composición de las regiones de captura, gráfica y resultados."""
from functools import partial

from nicegui import ui

from src.frontend.componentes.estructura_metodos_raices import montar_estructura_metodos_raices
from src.frontend.componentes.modos_captura_raices import MODO_BUSQUEDA, MODO_INTERVALO

MENSAJE_INICIAL = "Escribe la función y los extremos del intervalo."


def montar_contenido(vista):
    """Monta el ejercicio y devuelve sus regiones persistentes de salida."""
    return montar_estructura_metodos_raices(
        "Métodos cerrados", "Resuelve f(x) = 0 en un intervalo con Bisección o Regla falsa.",
        partial(_montar_captura, vista), partial(_montar_grafica, vista),
    )


def _montar_captura(vista) -> None:
    vista.captura.construir()
    vista.estado = ui.label(MENSAJE_INICIAL).classes("text-sm texto-secundario").props("role=status")
    vista.estado.bind_visibility_from(vista.modos, "value", backward=lambda modo: modo == MODO_INTERVALO)
    vista.continuidad.construir()
    vista.acciones.construir()


def _montar_grafica(vista) -> None:
    vista.grafica.construir()
    region = ui.column().classes("w-full min-w-0 gap-4").props('role=region aria-label="Resultados de la búsqueda"')
    with region.bind_visibility_from(vista.modos, "value", backward=lambda modo: modo == MODO_BUSQUEDA):
        vista.exploracion.construir_resultados()
