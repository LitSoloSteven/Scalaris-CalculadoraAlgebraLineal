"""Resumen y copia del resultado vigente, con precisión exclusivamente visual."""
from nicegui import ui

from src.backend.resolutores.raices.limites_raices import D_MAXIMO
from src.frontend.componentes.copia_resultado import renderizar_copia_resultado
from src.frontend.componentes.precision_presentacion import leer_precision_presentacion
from src.frontend.controladores.regla_falsa.diagnostico import detalles_diagnostico
from src.frontend.controladores.regla_falsa.presentacion import (
    aproximacion_presentada, avisos_resumen, etiqueta_aproximacion, metricas_resumen, titulo_estado,
)
from src.frontend.controladores.regla_falsa.salidas_regla_falsa import (
    datos_copia_regla_falsa, datos_copia_examen_regla_falsa,
)
from .modo_examen import crear_interruptor_examen


def mostrar_resultado(vista, respuesta: dict) -> None:
    """Presenta el sobre mediante texto escapado y conserva el estado real del motor."""
    with vista.contenedor_resultados:
        ui.label(titulo_estado(respuesta)).classes("text-xl font-bold texto-principal").props(
            "role=status aria-live=polite")
        ui.label(etiqueta_aproximacion(respuesta)).classes("texto-secundario")
        if respuesta["aproximacion"] is not None:
            _montar_formato(vista, respuesta)
        ui.label(respuesta["mensaje"]).classes(
            "texto-acento" if respuesta["estado"] == "EXITO" else "texto-advertencia")
        _mostrar_datos(metricas_resumen(respuesta))
        for aviso in avisos_resumen(respuesta):
            ui.label(aviso).classes("text-sm texto-advertencia")
        with ui.element("details").classes("regla-falsa-desplegable"):
            with ui.element("summary"):
                ui.label("Diagnóstico del cálculo")
            _mostrar_datos(detalles_diagnostico(respuesta))
        vista.interruptor_examen = crear_interruptor_examen(vista)
        renderizar_copia_resultado(lambda: (
            datos_copia_examen_regla_falsa if vista.modo_examen else datos_copia_regla_falsa
        )(respuesta, vista._precision_visual))


def _montar_formato(vista, respuesta: dict) -> None:
    vista.valor_aproximacion = ui.label(aproximacion_presentada(respuesta, vista._precision_visual)).classes(
        "regla-falsa-numero regla-falsa-aproximacion texto-principal")
    vista.formato = ui.number("Decimales de presentación", value=vista._precision_visual, min=0,
                              max=D_MAXIMO, step=1).classes("w-full matriz-entrada")
    vista.error_formato = ui.label().classes("text-sm texto-advertencia").props("role=alert")
    vista.formato.on_value_change(lambda: _actualizar_formato(vista, respuesta))
    ui.label("El formato cambia las cifras visibles; las iteraciones usan los valores internos.").classes(
        "text-sm texto-secundario")


def _actualizar_formato(vista, respuesta: dict) -> None:
    if vista.ultimo_resultado is not respuesta or vista.valor_aproximacion.is_deleted:
        return
    precision = leer_precision_presentacion(vista.formato, vista.error_formato)
    if precision is None:
        return
    vista._precision_visual = precision
    vista.valor_aproximacion.set_text(aproximacion_presentada(respuesta, precision))


def _mostrar_datos(datos: tuple) -> None:
    with ui.element("dl").classes("regla-falsa-metricas"):
        for etiqueta, valor in datos:
            with ui.element("dt"):
                ui.label(etiqueta).classes("text-sm texto-secundario")
            with ui.element("dd"):
                ui.label(valor).classes("regla-falsa-numero texto-principal")
