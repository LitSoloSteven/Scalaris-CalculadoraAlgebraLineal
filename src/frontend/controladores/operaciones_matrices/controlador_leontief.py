"""Orquestación serializable del modelo de Leontief."""
import json
from src.backend.resolutores.operaciones_matrices.captura_modelos import (
    parsear_matriz_modelo, parsear_vector_demanda, validar_nombres,
)
from src.backend.resolutores.operaciones_matrices.leontief import ResolutorModeloLeontief
from src.frontend.controladores.utilidades import parsear_carga_json


class ControladorLeontief:
    """Delega la captura y el cálculo económico al backend."""

    @staticmethod
    def procesar(carga_json: str) -> str:
        """Recibe coeficientes, demanda y nombres; devuelve resultado o error como JSON."""
        datos, error = parsear_carga_json(carga_json)
        if error:
            return error
        coeficientes = datos.get("matriz_coeficientes")
        if not coeficientes or not isinstance(coeficientes, list):
            return json.dumps({"estado": "ERROR", "mensaje": "Falta la matriz C."})
        demanda = datos.get("vector_demanda")
        if not demanda or not isinstance(demanda, list):
            return json.dumps({"estado": "ERROR", "mensaje": "Falta el vector d."})
        try:
            matriz = parsear_matriz_modelo(coeficientes, "C", cuadrada=True)
            vector_demanda = parsear_vector_demanda(demanda)
            nombres = validar_nombres(datos.get("nombres_sectores"), "nombres_sectores")
            resultado = ResolutorModeloLeontief().resolver(matriz, vector_demanda, nombres)
        except ValueError as error:
            resultado = {"estado": "ERROR", "mensaje": str(error)}
        return json.dumps(resultado, ensure_ascii=False, default=str)
