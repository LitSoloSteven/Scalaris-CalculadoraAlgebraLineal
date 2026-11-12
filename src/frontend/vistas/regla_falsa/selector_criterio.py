"""Selector de condición con un parámetro visible y borradores independientes."""
from nicegui import ui

from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS, condicion_criterio
from src.frontend.controladores.regla_falsa.configuracion_ampliada import criterio_capturado


def construir_selector(vista) -> None:
    """Monta los criterios del dominio sin estimar iteraciones ni alterar la precisión visual."""
    vista.criterio = ui.select({tipo: datos[0] for tipo, datos in CRITERIOS.items()},
                               value="residuo", label="Criterio de parada").classes("w-full matriz-entrada")
    vista.parametros_criterio = {"residuo": vista.tolerancia}
    vista.tolerancia.bind_visibility_from(vista.criterio, "value", backward=lambda tipo: tipo == "residuo")
    for tipo, (_, etiqueta, inicial) in CRITERIOS.items():
        if tipo != "residuo":
            campo = ui.input(etiqueta, value=str(inicial)).classes("w-full matriz-entrada").props(
                "inputmode=decimal maxlength=64 autocomplete=off")
            campo.bind_visibility_from(vista.criterio, "value", backward=lambda actual, tipo=tipo: actual == tipo)
            vista.parametros_criterio[tipo] = campo
            campo.on_value_change(lambda tipo=tipo: _editar_parametro(vista, tipo))
            campo.on("keydown.enter", vista.enviar_captura)
    vista.guia_criterio = ui.label().classes("text-sm texto-secundario").props("aria-live=polite")
    vista.criterio.on_value_change(lambda: _cambiar_criterio(vista))
    actualizar_guia(vista)


def actualizar_guia(vista) -> None:
    """Describe la condición activa sin evaluar la función ni convertir campos inactivos."""
    try:
        criterio = criterio_capturado({"criterio": capturar_criterio(vista), "limite_iteraciones": vista.limite.value})
        texto = condicion_criterio(criterio.tipo, criterio.parametro)
    except ValueError as error:
        texto = str(error)
    vista.guia_criterio.set_text(texto + " El residuo no acota el error en x; el ancho no garantiza el redondeo de la secante.")


def capturar_criterio(vista) -> dict:
    """Lee exclusivamente el campo del criterio seleccionado, sin interpretar su texto."""
    tipo = vista.criterio.value
    return {"tipo": tipo, "parametro": vista.parametros_criterio[tipo].value}


def _editar_parametro(vista, tipo: str) -> None:
    if vista.criterio.value == tipo and not vista._cargando_captura:
        actualizar_guia(vista)
        vista._editar()


def _cambiar_criterio(vista) -> None:
    actualizar_guia(vista)
    if not vista._cargando_captura:
        vista._editar()
