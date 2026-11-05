"""Controles del rango visual independiente de los extremos del método."""
from nicegui import ui

from src.frontend.controladores.biseccion.vista_previa import LONGITUD_CAMPO_GRAFICA, RANGO_GRAFICA_DEFECTO


def construir_rango(panel) -> None:
    """Monta extremos etiquetados, rango inicial explícito y copia voluntaria de a/b."""
    with ui.element("div").classes("biseccion-campos"):
        panel.minimo = _campo("Mínimo gráfico", RANGO_GRAFICA_DEFECTO[0])
        panel.maximo = _campo("Máximo gráfico", RANGO_GRAFICA_DEFECTO[1])
    ui.label(f"Rango visual independiente. Se inicia en [{RANGO_GRAFICA_DEFECTO[0]}, {RANGO_GRAFICA_DEFECTO[1]}]; puedes editarlo o copiar a y b.").classes(
        "text-sm texto-secundario")
    ui.button("Copiar a y b a la gráfica", color=None, on_click=panel.usar_intervalo).classes(
        "boton-discreto").props("ripple=false")


def _campo(etiqueta: str, valor: int):
    return ui.input(etiqueta, value=str(valor)).classes("w-full matriz-entrada").props(
        f"inputmode=decimal maxlength={LONGITUD_CAMPO_GRAFICA} autocomplete=off")
