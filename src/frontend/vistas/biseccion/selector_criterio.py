"""Controles contextuales del criterio activo, con guía consultada al dominio."""
from nicegui import ui

from src.backend.resolutores.raices.contrato_biseccion import D_MAXIMO, LIMITE_ITERACIONES_MAXIMO
from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS
from src.frontend.controladores.biseccion.captura_criterio import texto_condicion, texto_estimacion


def construir_selector(vista) -> None:
    """Monta un selector etiquetado y un único parámetro visible, conservando los campos ocultos."""
    with ui.element("div").classes("biseccion-campos"):
        _construir_campos(vista)
    vista.tolerancia = ui.label().classes("biseccion-tolerancia texto-acento").props("aria-live=polite")
    vista.estimacion = ui.label().classes("biseccion-numero text-sm texto-secundario").props("aria-live=polite")
    ui.label("Solo el criterio elegido determina la parada ordinaria. El residuo no es una cota del error en x; "
             "el ancho decimal no garantiza por sí solo el redondeo correcto.").classes("text-sm texto-secundario")


def _construir_campos(vista) -> None:
    vista.criterio = ui.select({tipo: datos[0] for tipo, datos in CRITERIOS.items()},
                               value="decimales", label="Criterio de parada").classes("w-full matriz-entrada")
    vista.parametros_criterio = {}
    with ui.column().classes("w-full gap-1"):
        for tipo, (_, etiqueta, inicial) in CRITERIOS.items():
            with ui.column().classes("w-full gap-1").bind_visibility_from(
                    vista.criterio, "value", backward=lambda actual, tipo=tipo: actual == tipo):
                campo = _campo_parametro(tipo, etiqueta, inicial)
                vista.parametros_criterio[tipo] = campo.classes("w-full matriz-entrada")
    vista.decimales = vista.parametros_criterio["decimales"]


def _campo_parametro(tipo, etiqueta, inicial):
    if tipo in ("decimales", "iteraciones"):
        maximo = D_MAXIMO if tipo == "decimales" else LIMITE_ITERACIONES_MAXIMO
        return ui.number(etiqueta, value=inicial, min=0 if tipo == "decimales" else 1, max=maximo, step=1)
    return ui.input(etiqueta, value=inicial).props("inputmode=decimal maxlength=64")


def enlazar_parametros(vista) -> None:
    """Vigila cambios y Enter en parámetros; los campos inactivos no invalidan resultados."""
    for tipo, campo in vista.parametros_criterio.items():
        campo.on_value_change(lambda tipo=tipo: _editar_parametro(vista, tipo))
        campo.on("keydown.enter", vista.enviar_calculo)
        campo.on("blur", lambda tipo=tipo: _validar_parametro(vista, tipo))


def actualizar_guia(vista, *, validar: bool = False) -> None:
    """Actualiza condición y estimación sin ejecutar la función matemática."""
    captura = vista.capturar()
    vista.criterio.props(f'title="{CRITERIOS[vista.criterio.value][0]}"')
    vista.tolerancia.set_text(texto_condicion(captura, mostrar_error=validar))
    vista.estimacion.set_text(texto_estimacion(captura, mostrar_error=validar))


def _validar_parametro(vista, tipo: str) -> None:
    if vista.criterio.value == tipo:
        actualizar_guia(vista, validar=True)


def _editar_parametro(vista, tipo: str) -> None:
    if vista.criterio.value == tipo:
        vista._editar()
