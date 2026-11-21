"""Composición de las regiones de captura, gráfica y resultados."""
from functools import partial
from types import SimpleNamespace

from nicegui import ui

from src.frontend.componentes.raices.captura.estructura_metodos_raices import montar_estructura_metodos_raices
from src.frontend.componentes.raices.captura.modos_captura_raices import MODO_BUSQUEDA, MODO_INTERVALO
from src.frontend.controladores.metodos_cerrados.adaptadores import REGLA_FALSA, captura_del_metodo
from src.frontend.vistas.regla_falsa.estados_entrada import EstadosEntrada

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
    vista.estados_entrada = _montar_estados_entrada(vista)
    vista.continuidad.construir()
    vista.acciones.construir()


def _montar_estados_entrada(vista) -> EstadosEntrada:
    captura = vista.captura
    controles = SimpleNamespace(
        estado=vista.estado, expresion=captura.expresion, inferior=captura.inferior, superior=captura.superior,
        unidad_angular=captura.unidad, limite=captura.limite, criterio=captura.criterio,
        tolerancia=captura.parametros_criterio["residuo"], parametros_criterio=captura.parametros_criterio,
        capturar=lambda: captura_del_metodo(captura.capturar()),
    )
    estados = EstadosEntrada(controles, lambda: captura.metodo_activo == REGLA_FALSA and not vista.en_busqueda)
    estados.construir()
    return estados


def _montar_grafica(vista) -> None:
    vista.grafica.construir()
    region = ui.column().classes("w-full min-w-0 gap-4").props('role=region aria-label="Resultados de la búsqueda"')
    with region.bind_visibility_from(vista.modos, "value", backward=lambda modo: modo == MODO_BUSQUEDA):
        vista.exploracion.construir_resultados()
