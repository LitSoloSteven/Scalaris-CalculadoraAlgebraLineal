"""Reconstruccion de matrices serializadas para presentar pasos exactos."""
from src.backend.modelos.matriz import Matriz


def reconstruir_matriz(datos: dict) -> Matriz:
    """Construye la matriz del paso con la validacion y aritmetica canonicas."""
    return Matriz(datos['filas'], datos['columnas'], datos['datos'])
