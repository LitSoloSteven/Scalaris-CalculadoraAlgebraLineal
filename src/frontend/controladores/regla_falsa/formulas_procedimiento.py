"""Proyección TeX de los valores finitos publicados por el motor de regla falsa."""
from src.frontend.controladores.biseccion.formato_expresion import numero_tex
from src.frontend.controladores.biseccion.presentacion import numero


def formulas_iteracion(fila: dict) -> tuple[str, ...]:
    """Describe la secante, su evaluación y el intervalo siguiente sin recalcular la aproximación."""
    valores = {clave: numero_tex(numero(fila[clave], True)) for clave in (
        "extremo_izquierdo", "extremo_derecho", "valor_izquierdo", "valor_derecho",
        "aproximacion", "valor_aproximacion", "residuo", "peso_secante",
    )}
    inferior, superior = valores["extremo_izquierdo"], valores["extremo_derecho"]
    izquierdo, derecho = valores["valor_izquierdo"], valores["valor_derecho"]
    secante = (r"c=a-\frac{f(a)(b-a)}{f(b)-f(a)}"
               rf"=({inferior})-\frac{{({izquierdo})[({superior})-({inferior})]}}{{({derecho})-({izquierdo})}}"
               rf"\approx {valores['aproximacion']}")
    siguiente = ",".join(numero_tex(numero(valor, True)) for valor in fila["intervalo_siguiente"])
    return (
        rf"[a,b]=[{inferior},{superior}]", secante,
        rf"w={valores['peso_secante']},\quad f(c)={valores['valor_aproximacion']}",
        rf"|f(c)|={valores['residuo']},\quad [a,b]_{{siguiente}}=[{siguiente}]",
    )
