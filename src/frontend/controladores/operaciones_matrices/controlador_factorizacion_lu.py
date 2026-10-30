"""Validación y delegación de la factorización LU."""
from typing import Any

from src.backend.resolutores.operaciones_matrices.factorizacion_lu import factorizar_lu
from src.backend.resolutores.sistemas_lineales.captura_coeficientes import capturar_coeficientes


class ControladorFactorizacionLU:
    """Procesa una captura matricial mediante el resolutor del dominio."""

    @staticmethod
    def procesar_captura(datos_crudos: dict) -> dict[str, Any]:
        """Valida la matriz de la captura y devuelve sus factores o un error de entrada."""
        try:
            matriz = capturar_coeficientes(datos_crudos.get("matriz_a"))
            return {**factorizar_lu(matriz), "filas": matriz.filas, "columnas": matriz.columnas}
        except ValueError as error:
            return {"estado": "ERROR", "mensaje": str(error)}
