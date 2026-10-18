"""Orquestación serializable del análisis de transformaciones lineales."""
import json
from src.backend.resolutores.operaciones_matrices.captura_modelos import (
    parsear_matriz_modelo, validar_nombres,
)
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales
from src.frontend.controladores.utilidades import parsear_carga_json


class ControladorTransformaciones:
    """Delega la captura y el análisis de núcleo e imagen al backend."""

    @staticmethod
    def procesar(carga_json: str) -> str:
        """Recibe matriz y nombres de variables; devuelve análisis o error como JSON."""
        datos, error = parsear_carga_json(carga_json)
        if error:
            return error
        datos_matriz = datos.get("matriz_transformacion")
        if not datos_matriz or not isinstance(datos_matriz, list):
            return json.dumps({"estado": "ERROR", "mensaje": "Falta la matriz A."})
        try:
            matriz = parsear_matriz_modelo(datos_matriz, "A")
            nombres = validar_nombres(datos.get("nombres_variables"), "nombres_variables")
            resultado = ResolutorTransformacionesLineales().resolver(matriz, nombres)
        except ValueError as error:
            resultado = {"estado": "ERROR", "mensaje": str(error)}
        return json.dumps(resultado, ensure_ascii=False, default=str)
