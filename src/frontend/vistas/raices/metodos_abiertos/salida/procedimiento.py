"""Renderizado de las fórmulas de planteamiento y de cada iteración."""
from nicegui import ui

from src.frontend.componentes.reproductor_pasos import renderizar_latex
from src.frontend.controladores.raices.compartido.formato.formato_funcion_real import formatear_expresion
from .resumen import _estado_visual


def renderizar_resumen_paso(paso, resultado: dict | None) -> None:
    """Muestra la función, sus parámetros destacados y la síntesis del paso."""
    if paso.tipo == "planteamiento" and resultado:
        _mostrar_funcion(resultado)
        _mostrar_parametros_planteamiento(resultado)
    elif paso.tipo == "resultado" and resultado:
        _mostrar_estado_resultado(resultado)
    ui.label(paso.explicacion).classes("text-sm texto-secundario")


def _mostrar_funcion(resultado: dict) -> None:
    entrada = resultado.get("entrada") or {}
    try:
        formula = formatear_expresion(entrada.get("expresion", ""))["latex"]
        renderizar_latex(formula, vigilar_region=True)
    except ValueError:
        return


def _mostrar_parametros_planteamiento(resultado: dict) -> None:
    entrada = resultado.get("entrada") or {}
    metodo = resultado.get("metodo")
    terminos = [("Método", "Newton-Raphson" if metodo == "newton" else "Secante")]
    if entrada.get("x0") is not None:
        terminos.append(("x₀", f"{entrada['x0']}"))
    if metodo == "secante" and entrada.get("x1") is not None:
        terminos.append(("x₁", f"{entrada['x1']}"))
    if entrada.get("tolerancia") is not None:
        terminos.append(("ε", f"{entrada['tolerancia']}"))
    if entrada.get("limite_iteraciones") is not None:
        terminos.append(("Máx. iter.", f"{entrada['limite_iteraciones']}"))
    _mostrar_banda_terminos(terminos, ultimo_destacado=False)


def _mostrar_estado_resultado(resultado: dict) -> None:
    etiqueta, clase, icono = _estado_visual(resultado.get("estado"))
    with ui.element("div").classes(f"metodos-abiertos-distintivo {clase}"):
        ui.icon(icono, size="xs")
        ui.label(etiqueta).classes("text-xs font-semibold")


def renderizar_iteracion(fila: dict, resultado: dict) -> None:
    """Expone los términos destacados y la sustitución numérica de la iteración."""
    metodo = resultado.get("metodo")
    _mostrar_terminos_iteracion(fila, metodo)
    if metodo == "newton" and fila.get("derivada") is not None:
        renderizar_latex(_formula_newton(fila), vigilar_region=True)
    elif metodo == "secante" and fila.get("x_anterior") is not None:
        renderizar_latex(_formula_secante(fila), vigilar_region=True)
    else:
        ui.label("Esta iteración terminó al detectar una condición numérica.").classes("text-sm")


_TERMINOS_COMUNES = (("x_n", "xₙ", ".6g"), ("f_x_n", "f(xₙ)", ".6g"))
_TERMINOS_METODO = {
    "newton": (_TERMINOS_COMUNES[0], _TERMINOS_COMUNES[1], ("derivada", "f'(xₙ)", ".6g")),
    "secante": (
        ("x_anterior", "xₙ₋₁", ".6g"),
        _TERMINOS_COMUNES[0],
        ("f_x_anterior", "f(xₙ₋₁)", ".6g"),
        _TERMINOS_COMUNES[1],
    ),
}


def _mostrar_terminos_iteracion(fila: dict, metodo: str | None) -> None:
    campos = _TERMINOS_METODO.get(metodo or "", _TERMINOS_COMUNES)
    terminos = [
        (etiqueta, f"{fila[clave]:{formato}}")
        for clave, etiqueta, formato in campos
        if fila.get(clave) is not None
    ]
    if fila.get("x_siguiente") is not None:
        terminos.append(("→ xₙ₊₁", f"{fila['x_siguiente']:.8g}"))
    if terminos:
        _mostrar_banda_terminos(terminos, ultimo_destacado=fila.get("x_siguiente") is not None)


def _mostrar_banda_terminos(terminos: list[tuple[str, str]], *, ultimo_destacado: bool) -> None:
    ultimo = len(terminos) - 1
    with ui.row().classes("metodos-abiertos-terminos w-full items-center gap-2 flex-wrap"):
        for indice, (simbolo, valor) in enumerate(terminos):
            destacado = ultimo_destacado and indice == ultimo
            clase = (
                "metodos-abiertos-termino metodos-abiertos-termino-destacado"
                if destacado else "metodos-abiertos-termino"
            )
            with ui.element("span").classes(clase):
                ui.label(simbolo).classes("metodos-abiertos-termino-simbolo text-xs")
                ui.label(valor).classes("metodos-abiertos-termino-valor text-xs")


def _formula_newton(fila: dict) -> str:
    return (rf"x_{{n+1}}={fila['x_n']:.8g}-\frac{{{fila['f_x_n']:.8g}}}"
            rf"{{{fila['derivada']:.8g}}}={fila['x_siguiente']:.8g}")


def _formula_secante(fila: dict) -> str:
    diferencia_x = fila["x_n"] - fila["x_anterior"]
    diferencia_y = fila["f_x_n"] - fila["f_x_anterior"]
    return (rf"x_{{n+1}}={fila['x_n']:.8g}-\frac{{{fila['f_x_n']:.8g}"
            rf"({diferencia_x:.8g})}}{{{diferencia_y:.8g}}}={fila['x_siguiente']:.8g}")
