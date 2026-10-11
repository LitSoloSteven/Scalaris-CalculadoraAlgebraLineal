"""Controlador de determinantes (pendiente de decisión de producto en frontend)."""
from typing import Any

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.determinante import (
    ResolutorDeterminante,
)


class ControladorDeterminante:
    """Gestiona la recomendación de método y cálculo pedagógico de determinantes."""

    @staticmethod
    def obtener_recomendacion(datos_matriz: list[list[Any]]) -> dict[str, Any]:
        """Devuelve el método recomendado para calcular el determinante de la matriz."""
        return ResolutorDeterminante.recomendar_metodo(datos_matriz)

    @staticmethod
    def procesar(datos_matriz: list[list[Any]], metodo: str = "auto") -> dict[str, Any]:
        """Calcula el determinante usando el algoritmo especificado o recomendado."""
        n = len(datos_matriz)
        matriz = Matriz(n, n, datos_matriz)
        recomendacion = ResolutorDeterminante.recomendar_metodo(datos_matriz)

        metodo_efectivo = metodo
        if metodo_efectivo == "auto":
            metodo_efectivo = recomendacion["metodo_recomendado"]

        if metodo_efectivo == "laplace":
            resultado = ResolutorDeterminante.resolver_laplace(matriz)
        else:
            resultado = ResolutorDeterminante.resolver_lu(matriz)

        resultado["recomendacion"] = recomendacion
        return resultado
