"""Presentación de factores y comprobación entregados por el dominio."""
from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_LATEX_INVERSA
from src.frontend import textos
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_matriz


def mostrar_factores_lu(resultado: dict) -> None:
    """Muestra los factores de resultado y la comprobación sin recalcularlos."""
    factores = (resultado["permutacion"], resultado["inferior"], resultado["superior"])
    with ui.element("div").classes("factorizacion-lu-factores"):
        for nombre, matriz, lectura, formula in zip(("P", "L", "U"), factores, textos.LU_LECTURAS, resultado["formulas_resultado"]):
            with ui.column().classes("factorizacion-lu-factor min-w-0"):
                ui.label(f"{nombre} · {matriz.filas} × {matriz.columnas}").classes("font-bold sesion-numero")
                ui.label(lectura).classes("texto-secundario")
                if max(matriz.filas, matriz.columnas) <= DIMENSION_MAXIMA_LATEX_INVERSA:
                    renderizar_latex(formula)
                else:
                    ui.html(html_tabla_matriz(matriz))
    veredicto = textos.LU_CORRECTO if resultado["comprobacion"]["coincide"] else textos.LU_INCORRECTO
    ui.label(textos.LU_VEREDICTO.format(veredicto=veredicto)).props('role="status"').classes("font-bold sesion-numero")
