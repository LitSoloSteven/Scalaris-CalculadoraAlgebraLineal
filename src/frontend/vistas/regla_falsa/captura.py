"""Controles etiquetados para la captura cruda del método de regla falsa."""
from nicegui import ui

from src.backend.resolutores.raices.limites_raices import LONGITUD_MAXIMA_EXPRESION
from src.backend.resolutores.raices.unidades_angulares import UNIDADES_ANGULARES
from .estado_captura import PREFERENCIAS_INICIALES
from .modos_captura import MODO_INTERVALO, construir_modos, region_modo
from .selector_criterio import construir_selector


def construir_captura(vista) -> None:
    """Monta expresión, extremos y preferencias sin interpretar los valores introducidos."""
    vista.expresion = ui.input("Función f(x)", placeholder="Ejemplo: x^2 - 2").classes(
        "w-full matriz-entrada").props(f"maxlength={LONGITUD_MAXIMA_EXPRESION} autocomplete=off spellcheck=false")
    vista.unidad_angular = ui.select(
        {unidad: unidad.capitalize() for unidad in UNIDADES_ANGULARES},
        value=PREFERENCIAS_INICIALES["unidad_angular"], label="Unidad trigonométrica",
    ).classes("w-full matriz-entrada")
    construir_modos(vista)
    with region_modo(vista, MODO_INTERVALO):
        with ui.element("div").classes("regla-falsa-campos"):
            vista.inferior = _campo("Extremo a")
            vista.superior = _campo("Extremo b")
    _construir_parada(vista)
    with region_modo(vista, MODO_INTERVALO):
        vista.boton_resolver = ui.button("Calcular raíz", icon="calculate", color=None,
                                        on_click=vista.resolver).classes("boton-principal").props("ripple=false")


def _construir_parada(vista) -> None:
    with ui.element("div").classes("regla-falsa-campos"):
        vista.tolerancia = _campo("Tolerancia de residuo", PREFERENCIAS_INICIALES["tolerancia"])
        vista.limite = _campo("Límite de iteraciones", PREFERENCIAS_INICIALES["limite_iteraciones"])
    construir_selector(vista)


def _campo(etiqueta: str, valor: str = ""):
    return ui.input(etiqueta, value=valor).classes("w-full matriz-entrada").props(
        "inputmode=decimal maxlength=64 autocomplete=off")
