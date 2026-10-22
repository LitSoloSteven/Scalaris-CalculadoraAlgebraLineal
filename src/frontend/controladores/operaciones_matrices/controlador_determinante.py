"""Validación y delegación del cálculo pedagógico de determinantes."""
from typing import Any

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.determinante import (
    ResolutorDeterminante,
)
from src.backend.resolutores.operaciones_matrices.captura_inversa import validar_y_parsear_matriz_cuadrada


class ControladorDeterminante:
    """Gestiona la recomendación de método y cálculo pedagógico de determinantes."""

    @staticmethod
    def obtener_recomendacion(datos_matriz: list[list[Any]]) -> dict[str, Any]:
        """Devuelve el método recomendado para calcular el determinante de la matriz."""
        return ResolutorDeterminante.recomendar_metodo(datos_matriz)

    @staticmethod
    def procesar(datos_matriz: list[list[Any]], metodo: str = "auto") -> dict[str, Any]:
        """Calcula el determinante usando el algoritmo especificado o recomendado."""
        if metodo not in ("auto", "laplace", "lu"):
            raise ValueError("Metodo no reconocido. Elige cofactores o eliminacion con pivoteo.")
        dimension = len(datos_matriz)
        matriz = Matriz(dimension, dimension, datos_matriz)
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

    @staticmethod
    def recomendar_captura(datos_crudos: dict) -> dict[str, Any]:
        """Valida la captura y recomienda sin ejecutar ni cambiar el metodo de calculo."""
        matriz, _, error = validar_y_parsear_matriz_cuadrada(datos_crudos)
        if error:
            return error
        return {"estado": "EXITO", **ControladorDeterminante.obtener_recomendacion(matriz.datos)}

    @staticmethod
    def procesar_captura(datos_crudos: dict) -> dict[str, Any]:
        """Valida captura y respeta el metodo elegido; devuelve errores sin sustituirlo."""
        matriz, _, error = validar_y_parsear_matriz_cuadrada(datos_crudos)
        if error:
            return error
        try:
            resultado = ControladorDeterminante.procesar(matriz.datos, metodo=datos_crudos.get("metodo", "lu"))
        except ValueError as error:
            return {"estado": "ERROR", "mensaje": str(error), "pasos": []}
        return {"estado": "EXITO", **resultado}
