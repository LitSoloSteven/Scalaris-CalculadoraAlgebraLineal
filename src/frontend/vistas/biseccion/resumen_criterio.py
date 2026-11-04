"""Resumen centrado en el estado, con formato visual independiente del cálculo."""
from nicegui import ui

from src.backend.resolutores.raices.contrato_biseccion import D_MAXIMO
from src.frontend.componentes.copia_resultado import renderizar_copia_resultado
from src.frontend.controladores.biseccion.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.biseccion.captura_criterio import precision_presentacion
from src.frontend.controladores.biseccion.presentacion import motivo
from src.frontend.controladores.biseccion.presentacion_criterio import (
    aproximacion_presentada, avisos_resumen, metricas_resumen, texto_resumen, titulo_estado,
)


def mostrar_resumen(vista, respuesta: dict) -> None:
    """Monta estado y magnitudes, con un control de formato que no invalida el resultado."""
    with ui.column().classes("panel-tarjeta p-6 w-full gap-3"):
        ui.label(titulo_estado(respuesta)).classes("text-xl font-bold texto-principal").props("role=status aria-live=polite")
        for aviso in avisos_resumen(respuesta):
            ui.label(aviso).classes("text-sm texto-advertencia").props("role=status aria-live=polite")
        if respuesta.get("aproximacion") is None:
            ui.label(respuesta["mensaje"]).classes("texto-advertencia").props("role=alert")
            _mostrar_metricas(respuesta)
            return
        precision = getattr(vista, "_precision_visual", DECIMALES_PRESENTACION_DEFECTO)
        vista.formato = ui.number("Decimales de presentación", value=precision, min=0,
                                  max=D_MAXIMO, step=1).classes("w-full matriz-entrada")
        vista.error_formato = ui.label().classes("text-sm texto-advertencia").props("role=alert")
        vista.detalle_resumen = ui.column().classes("w-full gap-3")
        with vista.detalle_resumen:
            _mostrar_detalle(respuesta, precision)
        vista.formato.on_value_change(lambda: _actualizar_formato(vista, respuesta))


def _mostrar_detalle(respuesta: dict, precision: int) -> None:
    provisional = respuesta["estado"] != "EXITO"
    ui.label("Aproximación provisional" if provisional else "Aproximación de la raíz").classes("texto-secundario")
    ui.label(aproximacion_presentada(respuesta, precision)).classes("biseccion-aproximacion texto-principal")
    ui.label(motivo(respuesta)).classes("texto-advertencia" if provisional else "texto-acento")
    _mostrar_metricas(respuesta)
    ui.label("El formato no determina la parada. La tabla conserva hasta 17 cifras; "
             "el residuo no es una cota del error en x.").classes("text-sm texto-secundario")
    renderizar_copia_resultado({"estado": respuesta["estado"], "solucion": texto_resumen(respuesta, precision)})


def _mostrar_metricas(respuesta: dict) -> None:
    with ui.element("div").classes("biseccion-metricas"):
        for etiqueta, valor in metricas_resumen(respuesta):
            with ui.column().classes("gap-1 min-w-0"):
                ui.label(etiqueta).classes("text-sm texto-secundario")
                ui.label(valor).classes("biseccion-numero texto-principal")


def _actualizar_formato(vista, respuesta: dict) -> None:
    if vista.detalle_resumen.is_deleted or vista.ultimo_resultado is not respuesta:
        return
    try:
        precision = precision_presentacion(vista.formato.value)
    except ValueError as error:
        vista.error_formato.set_text(str(error))
        return
    vista.error_formato.set_text("")
    vista._precision_visual = precision
    vista.detalle_resumen.clear()
    with vista.detalle_resumen:
        _mostrar_detalle(respuesta, precision)
