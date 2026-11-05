"""Metadatos de captura obtenidos de la gramática de funciones reales."""
import ast

from src.backend.resolutores.raices.gramatica_funcion import analizar_expresion
from src.backend.resolutores.raices.unidades_angulares import funcion_sensible_a_unidad


def sensible_a_unidad(expresion: str) -> bool:
    """Consulta las llamadas de la expresión validada; propaga ValueError de sintaxis o capacidad."""
    return any(
        isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
        and funcion_sensible_a_unidad(nodo.func.id)
        for nodo in ast.walk(analizar_expresion(expresion))
    )
