"""Presentación de estados, resúmenes y tablas separados por identificador."""
from nicegui import ui

from src.frontend.componentes.copia_resultado import renderizar_copia_resultado
from src.frontend.controladores.biseccion.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.biseccion.presentacion_criterio import datos_copia_biseccion, texto_resumen, titulo_estado
from .resultado import mostrar_tabla


def mostrar_resultados_multiples(lote: dict) -> None:
    """Compone el lote actual sin sobrescribir el resultado individual ni su contexto de Glosa."""
    for aviso in lote["advertencias"]:
        ui.label(aviso).classes("text-sm texto-secundario")
    ui.label(f"Unidad angular: {lote['unidad_angular']} · Filas generadas: {lote['filas_generadas']}").classes(
        "biseccion-numero texto-secundario")
    ui.label(f"Reserva de evaluaciones: {lote['evaluaciones_reservadas']} de {lote['presupuesto_evaluaciones']}. "
             "Es una cota conservadora, no el número de evaluaciones efectivas.").classes(
                 "biseccion-numero text-sm texto-secundario")
    if lote["presupuesto_agotado"]:
        ui.label("El presupuesto se agotó. Los candidatos pendientes están identificados; puedes resolverlos uno por uno.").classes(
            "texto-advertencia").props("role=status")
    for registro in lote["resultados"]:
        _mostrar_registro(registro)


def _mostrar_registro(registro: dict) -> None:
    respuesta = registro["respuesta"]
    titulo = titulo_estado(respuesta) if respuesta is not None else registro["estado"].replace("_", " ").capitalize()
    with ui.expansion(f"{registro['identificador']} · {titulo}").classes("biseccion-resultado-multiple w-full"):
        if respuesta is None:
            ui.label(registro["mensaje"]).classes("texto-advertencia")
            return
        resumen = texto_resumen(respuesta, DECIMALES_PRESENTACION_DEFECTO)
        for linea in resumen.splitlines():
            ui.label(linea).classes("biseccion-numero text-sm texto-principal")
        renderizar_copia_resultado(datos_copia_biseccion(respuesta["estado"], f"{registro['identificador']}\n{resumen}"))
        if respuesta.get("iteraciones"):
            mostrar_tabla(respuesta)
