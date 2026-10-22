"""Captura acotada de familias vectoriales para el analisis de independencia."""
from src.backend.constantes import DIMENSION_MAXIMA_VECTORES
from src.backend.modelos.matriz import Matriz
from .captura import construir_vector_desde_diccionario
from .independencia import validar_cantidad_vectores


def capturar_independencia(vectores: object) -> list[Matriz]:
    """Convierte columnas crudas usando el parser comun; ValueError ante forma, coste o celda invalidos."""
    if not isinstance(vectores, dict):
        raise ValueError("La captura debe ser un objeto de vectores.")
    validar_cantidad_vectores(len(vectores))
    for vector in vectores.values():
        if not isinstance(vector, dict) or not isinstance(vector.get("datos"), list):
            raise ValueError("Cada vector debe contener una lista de componentes.")
        if len(vector["datos"]) > DIMENSION_MAXIMA_VECTORES:
            raise ValueError(f"Cada vector admite hasta {DIMENSION_MAXIMA_VECTORES} componentes.")
    return [construir_vector_desde_diccionario(vector) for vector in vectores.values()]
