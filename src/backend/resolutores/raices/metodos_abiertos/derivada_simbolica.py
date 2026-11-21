"""Derivación simbólica de expresiones que pueden volver a compilarse."""
import ast

from ..gramatica_funcion import analizar_expresion
from ..nodos_derivada import proteger_derivada
from ..nodos_integral import es_integral
from ..normalizacion_funcion import normalizar_expresion
from ..reglas_derivacion import ErrorDerivadaNoDisponible as ErrorDerivadaNoDisponible, derivar_nodo


class ErrorDerivadaDemasiadoGrande(ValueError):
    """Indica que la derivada excede los límites de la gramática."""


def derivar_expresion(expresion: str) -> str:
    """Devuelve f'(x) normalizada y validada; lanza ValueError si no se puede derivar."""
    arbol = analizar_expresion(expresion)
    derivada = derivar_nodo(arbol.body)
    if any(es_integral(nodo) for nodo in ast.walk(arbol)):
        derivada = proteger_derivada(arbol.body, derivada)
    try:
        texto = ast.unparse(ast.Expression(body=derivada))
    except (ValueError, RecursionError) as error:
        raise ErrorDerivadaNoDisponible("No se pudo construir la expresión de la derivada.") from error
    try:
        normalizada = normalizar_expresion(texto)
        analizar_expresion(normalizada)
    except ValueError as error:
        raise ErrorDerivadaDemasiadoGrande(
            "La derivada simbólica excede los límites de la gramática "
            "(512 caracteres, 256 nodos o 32 niveles)."
        ) from error
    return normalizada
