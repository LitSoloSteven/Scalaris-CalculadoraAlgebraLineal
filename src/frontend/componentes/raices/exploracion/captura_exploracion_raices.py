"""Campos de rango visual con etiquetas y límites compartidos."""
from nicegui import ui

from src.frontend.componentes.aplicacion.base.simbolos import habilitar_simbolos
from src.frontend.controladores.raices.compartido.formato.rango_exploracion_raices import LONGITUD_CAMPO_GRAFICA, RANGO_GRAFICA_DEFECTO


def campos_rango(contexto: str, clase_contenedor: str) -> tuple:
    """Monta extremos del rango con contexto accesible y estilo del consumidor."""
    with ui.element("div").classes(clase_contenedor):
        minimo = _campo(f"Mínimo del {contexto}", RANGO_GRAFICA_DEFECTO[0])
        maximo = _campo(f"Máximo del {contexto}", RANGO_GRAFICA_DEFECTO[1])
    return minimo, maximo


def _campo(etiqueta: str, valor: int):
    campo = ui.input(etiqueta, value=str(valor)).classes("w-full matriz-entrada").props(
        f"inputmode=decimal maxlength={LONGITUD_CAMPO_GRAFICA} autocomplete=off")
    habilitar_simbolos(campo, "real")
    return campo
