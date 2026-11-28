"""Paginación en servidor y formato de la página visible de la traza."""
from nicegui import ui

from src.frontend.componentes.raices.resultados.tabla_iteraciones import (
    PaginacionIteraciones,
    presentar_tabla_iteraciones,
)
from src.frontend.controladores.raices.biseccion.presentacion.presentacion import COLUMNAS, filas_tabla
from src.frontend.controladores.raices.biseccion.salidas.salidas_biseccion import COLUMNAS_EXAMEN, datos_examen


def mostrar_tabla(respuesta: dict, examen: ui.switch | ui.checkbox | None = None) -> None:
    """Monta una tabla desplazable que solo recibe las filas de la página actual."""
    with ui.column().classes("panel-tarjeta p-5 w-full min-w-0"):
        ui.label("Tabla de iteraciones").classes("text-xl font-bold")
        ui.label("Ancho: b−a. Cota: (b−a)/2 en x, si f es continua. Residuo: |f(c)|. Error relativo: |(cᵢ−cᵢ₋₁)/cᵢ|·100%; no aplica en la primera fila o si cᵢ=0.").classes("text-sm texto-secundario")
        precision = ui.switch("Inspeccionar valores internos (hasta 17 cifras)")
        with ui.element("div").classes("biseccion-tabla w-full"):
            tabla = ui.table(columns=[], rows=[], row_key="i", pagination=0)
            presentar_tabla_iteraciones(tabla, paginacion_propia=True)
        preparar = lambda inicio, fin: _preparar_pagina(respuesta, precision, examen, inicio, fin)
        preferencias = (precision,) if examen is None else (precision, examen)
        paginacion = PaginacionIteraciones(tabla, len(respuesta["iteraciones"]), preparar, preferencias)
        paginacion.construir()


def _preparar_pagina(respuesta, precision, examen, inicio: int, fin: int) -> tuple:
    originales = respuesta["iteraciones"][inicio:fin]
    en_examen = examen is not None and examen.value
    columnas = COLUMNAS + COLUMNAS_EXAMEN if en_examen else COLUMNAS
    filas = filas_tabla({"iteraciones": originales}, precision.value)
    if en_examen:
        for fila, original in zip(filas, originales):
            fila.update(datos_examen(original, respuesta["estado"]))
    return columnas, filas
