"""Fórmulas de una iteración obtenidas de sus valores publicados."""
from .formato_expresion import numero_tex
from .presentacion import numero


def formulas_iteracion(fila: dict) -> tuple[str, ...]:
    """Proyecta intervalo, sustitución y evaluaciones sin recalcular el punto medio."""
    def _mostrar(clave: str) -> str:
        return numero_tex(numero(fila[clave], True))

    inferior, superior, medio = (_mostrar(clave) for clave in ("extremo_izquierdo", "extremo_derecho", "c"))
    intervalo = rf"[a,b]=[{inferior},{superior}]"
    punto_medio = rf"c=\frac{{a+b}}{{2}}=\frac{{({inferior})+({superior})}}{{2}}\approx {medio}"
    evaluaciones = rf"f(a)={_mostrar('f_a')},\quad f(b)={_mostrar('f_b')},\quad f(c)={_mostrar('f_c')}"
    formulas = (intervalo, punto_medio, evaluaciones)
    signo = {-1: "<", 0: "=", 1: ">"}.get(fila.get("signo_producto"))
    if signo is not None:
        formulas += (rf"f(a)\cdot f(c){signo}0",)
    accion = fila.get("accion")
    if accion == "reemplazar_b":
        formulas += (rf"[a,c]=[{inferior},{medio}]",)
    elif accion == "reemplazar_a":
        formulas += (rf"[c,b]=[{medio},{superior}]",)
    return formulas
