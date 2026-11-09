"""Ejemplos, limpieza y restauración explícita de cálculos de esta sesión."""
from nicegui import ui

from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.vistas.biseccion.acciones_captura import desplegable
from .ejemplos import EJEMPLOS


def construir_acciones(vista) -> None:
    """Monta ejemplos identificados y la confirmación de limpieza reutilizable."""
    with desplegable("Ejemplos").classes("regla-falsa-desplegable"):
        ui.label("Carga un ejemplo y pulsa Calcular raíz.").classes("text-sm texto-secundario")
        with ui.row().classes("w-full gap-2"):
            for etiqueta, captura in EJEMPLOS:
                ui.button(etiqueta, color=None, on_click=lambda captura=captura: vista.cargar_captura(
                    captura)).classes("boton-discreto").props("ripple=false")
    vista.limpieza = crear_boton_limpieza(vista, lambda: not vista.contenedor_resultados.is_deleted,
                                         animar=False, campo_foco=vista.expresion)


def mostrar_recientes(vista) -> None:
    """Reconstruye los cinco registros reales conservados por el historial de sesión."""
    vista.recientes.clear()
    with vista.recientes:
        ui.label("Recientes de esta sesión").classes("font-semibold texto-principal")
        if not vista.historial:
            ui.label("Los cálculos con aproximación o filas válidas aparecerán aquí.").classes(
                "text-sm texto-secundario")
        for calculo in vista.historial:
            captura = calculo["captura"]
            ui.button(calculo["titulo"], color=None,
                      on_click=lambda captura=captura: vista.cargar_captura(captura)).classes(
                          "boton-discreto").props("ripple=false").tooltip(
                              f"{captura['expresion']} · {captura['unidad_angular']} · tolerancia {captura['tolerancia']}")
