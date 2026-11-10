"""Montaje del panel exploratorio mediante acciones del consumidor."""
from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from src.frontend.controladores.exploracion_raices import PASO_EXPLORACION_DEFECTO

ESTADO_INICIAL = "Define un rango y un paso para explorar la función."


@dataclass(frozen=True)
class MontajeExploracion:
    """Funciones de montaje y clases visuales, sin referencias a vistas concretas."""

    campos_rango: Callable
    desplegable: Callable
    vincular_envio: Callable
    clase_panel: str
    clase_resultados: str
    enviar_desde_boton: Callable
    campos_captura: Callable
    editar_rango: Callable
    crear_campo: Callable


def construir_exploracion(panel, montaje: MontajeExploracion) -> None:
    """Construye controles y conecta las acciones públicas del panel recibido."""
    with ui.column().classes(f"panel-tarjeta {montaje.clase_panel} w-full gap-4 p-6"):
        ui.label("Explorar intervalos").classes("text-xl font-semibold texto-principal")
        ui.label("Busca candidatos en el rango del gráfico. Los extremos del cálculo cambian al cargar un intervalo.").classes(
            "text-sm texto-secundario")
        panel.minimo, panel.maximo = montaje.campos_rango("rango de búsqueda")
        _construir_paso(panel, montaje)
        with ui.row().classes("w-full gap-3"):
            panel.boton = ui.button("Explorar candidatos", color=None).classes("boton-principal").props("ripple=false")
            montaje.vincular_envio(panel.boton, montaje.enviar_desde_boton)
        panel.estado = ui.label(ESTADO_INICIAL).classes("texto-secundario").props("role=status aria-live=polite")
        panel.contenedor_resultados = ui.column().classes(f"{montaje.clase_resultados} w-full gap-4")
    for campo in montaje.campos_captura():
        campo.on("keydown.enter", panel.enviar_busqueda)
    panel.paso.on_value_change(montaje.editar_rango)
    panel.actualizar_paso()


def _construir_paso(panel, montaje: MontajeExploracion) -> None:
    with montaje.desplegable("Avanzado"):
        panel.paso = montaje.crear_campo("Paso h", PASO_EXPLORACION_DEFECTO)
        panel.etiqueta_paso = ui.label().classes("text-sm texto-secundario")
        ui.button("Volver a automático", color=None, on_click=panel.restablecer_paso).classes("boton-discreto")
