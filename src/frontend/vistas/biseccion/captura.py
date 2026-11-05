"""Función compartida y captura del intervalo individual."""
from nicegui import ui

from src.backend.resolutores.raices.contrato_biseccion import LONGITUD_MAXIMA_EXPRESION
from .movimiento import modalidad_puntero, vincular_envio
from .selector_criterio import construir_selector
from .selector_unidad import construir_selector_unidad

GUIA_CONTINUIDAD = "La garantía requiere continuidad en todo [a, b]. Un cambio de signo y una gráfica muestreada no demuestran continuidad."


def construir_captura(vista) -> None:
    """Monta la función y su unidad en una fila adaptable."""
    with ui.element("div").classes("biseccion-funcion w-full"):
        vista.expresion = ui.input("Función f(x)", placeholder="Ejemplo: x^2 - 2").classes(
            "w-full matriz-entrada").props(f"maxlength={LONGITUD_MAXIMA_EXPRESION} autocomplete=off spellcheck=false")
        construir_selector_unidad(vista)
    vista.estado_expresion = _region_estado()


def construir_intervalo(vista) -> None:
    """Monta los extremos vacíos, el criterio y la acción del cálculo individual."""
    with ui.element("div").classes("biseccion-campos"):
        vista.inferior = _campo_extremo("Extremo inferior a")
        vista.superior = _campo_extremo("Extremo superior b")
    vista.estado_continuidad = _region_estado()
    construir_selector(vista)


def construir_boton_calculo(vista) -> None:
    """Monta el envío del cálculo después de las opciones avanzadas."""
    async def _enviar(evento) -> None:
        await vista.enviar_calculo(puntero=modalidad_puntero(evento) is True)

    vista.boton_resolver = ui.button("Calcular raíz", icon="calculate", color=None).classes(
        "boton-principal").props("ripple=false")
    vincular_envio(vista.boton_resolver, _enviar)


def _campo_extremo(etiqueta: str):
    return ui.input(etiqueta).classes("w-full matriz-entrada").props("inputmode=decimal maxlength=64 autocomplete=off")


def _region_estado():
    return ui.label().classes("text-sm texto-secundario").props("role=status aria-live=polite")
