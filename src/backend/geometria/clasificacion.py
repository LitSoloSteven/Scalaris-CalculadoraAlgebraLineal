"""Clasificación de ecuaciones lineales y análisis de paralelismo geométrico."""
from fractions import Fraction


def clasificar_ecuacion(
    coeficientes: list[Fraction],
    termino_independiente: Fraction,
    dimension: int,
) -> str:
    """Clasifica una ecuación según sus coeficientes y dimensión."""
    if all(c == 0 for c in coeficientes):
        if termino_independiente == 0:
            return "trivial"
        return "contradiction"
    if dimension == 2:
        return "line"
    if dimension == 3:
        return "plane"
    return "line"


def son_proporcionales(
    fila_a: list[Fraction],
    fila_b: list[Fraction],
) -> bool:
    """Verifica si dos vectores de coeficientes son linealmente dependientes."""
    razon: Fraction | None = None
    for elemento_a, elemento_b in zip(fila_a, fila_b):
        if elemento_a == 0 and elemento_b == 0:
            continue
        if elemento_a == 0 or elemento_b == 0:
            return False
        razon_actual = Fraction(elemento_b, elemento_a)
        if razon is None:
            razon = razon_actual
        elif razon_actual != razon:
            return False
    return razon is not None


def _par_es_incompatible(
    fila_a: list[Fraction],
    fila_b: list[Fraction],
    indep_a: Fraction,
    indep_b: Fraction,
) -> bool:
    """Determina si un par de ecuaciones con coeficientes proporcionales no tiene solución."""
    if not son_proporcionales(fila_a, fila_b):
        return False
    razon: Fraction | None = None
    for elemento_a, elemento_b in zip(fila_a, fila_b):
        if elemento_a != 0:
            razon = Fraction(elemento_b, elemento_a)
            break
    if razon is None:
        return False
    return indep_b != razon * indep_a


def detectar_paralelismo(
    coeficientes: list[list[Fraction]],
    terminos_indep: list[Fraction],
) -> bool:
    """Detecta si hay al menos dos ecuaciones paralelas e incompatibles."""
    cantidad_filas = len(coeficientes)
    if cantidad_filas < 2:
        return False
    for i in range(cantidad_filas):
        for j in range(i + 1, cantidad_filas):
            if _par_es_incompatible(
                coeficientes[i],
                coeficientes[j],
                terminos_indep[i],
                terminos_indep[j],
            ):
                return True
    return False
