"""Renderizado de las fórmulas de planteamiento y de cada iteración."""
from nicegui import ui

from src.frontend.controladores.formato_funcion_real import formatear_expresion
from src.frontend.componentes.reproductor_pasos import renderizar_latex


def renderizar_resumen_paso(paso, resultado: dict | None) -> None:
    """Muestra la función capturada en el planteamiento y el texto del paso."""
    if paso.tipo == "planteamiento" and resultado:
        _mostrar_funcion(resultado)
    ui.label(paso.explicacion).classes("text-sm texto-secundario")


def _mostrar_funcion(resultado: dict) -> None:
    entrada = resultado.get("entrada") or {}
    try:
        formula = formatear_expresion(entrada.get("expresion", ""))["latex"]
        renderizar_latex(formula, vigilar_region=True)
    except ValueError:
        return


def renderizar_iteracion(fila: dict, resultado: dict) -> None:
    """Expone la sustitución numérica correspondiente a la iteración activa."""
    metodo = resultado.get("metodo")
    if metodo == "newton" and fila.get("derivada") is not None:
        renderizar_latex(_formula_newton(fila), vigilar_region=True)
    elif metodo == "secante" and fila.get("x_anterior") is not None:
        renderizar_latex(_formula_secante(fila), vigilar_region=True)
    else:
        ui.label("Esta iteración terminó al detectar una condición numérica.").classes("text-sm")


def _formula_newton(fila: dict) -> str:
    return (rf"x_{{n+1}}={fila['x_n']:.8g}-\frac{{{fila['f_x_n']:.8g}}}"
            rf"{{{fila['derivada']:.8g}}}={fila['x_siguiente']:.8g}")


def _formula_secante(fila: dict) -> str:
    diferencia_x = fila["x_n"] - fila["x_anterior"]
    diferencia_y = fila["f_x_n"] - fila["f_x_anterior"]
    return (rf"x_{{n+1}}={fila['x_n']:.8g}-\frac{{{fila['f_x_n']:.8g}"
            rf"({diferencia_x:.8g})}}{{{diferencia_y:.8g}}}={fila['x_siguiente']:.8g}")
