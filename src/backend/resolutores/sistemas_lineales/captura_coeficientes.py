"""Captura rectangular de coeficientes reutilizando la validacion de sistemas."""
import json

from src.backend.modelos.matriz import Matriz
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS
from .captura import validar_y_construir_aumentada


def capturar_coeficientes(datos: object) -> Matriz:
    """Valida forma, limites y celdas exactas; devuelve A o lanza ValueError con coordenadas."""
    if not isinstance(datos, list):
        raise ValueError("La matriz debe ser una lista de filas.")
    if len(datos) > DIMENSION_MAXIMA_SISTEMAS:
        raise ValueError(f"La matriz admite hasta {DIMENSION_MAXIMA_SISTEMAS} filas.")
    _, coeficientes, _, filas, columnas, error = validar_y_construir_aumentada(
        {"matriz_a": datos, "vector_b": ["0"] * len(datos)})
    if error:
        raise ValueError(json.loads(error)["mensaje"])
    return Matriz(filas, columnas, coeficientes)
