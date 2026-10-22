"""Adaptacion de la captura vectorial a la prueba exacta de independencia."""
import json

from src.backend.resolutores.operaciones_vectores.captura_independencia import capturar_independencia
from src.backend.resolutores.operaciones_vectores.independencia import analizar_independencia
from src.frontend.controladores.operaciones_matrices.codificador import CodificadorMatriz


def procesar_independencia(vectores: dict) -> str:
    """Valida limites y columnas; devuelve resultado serializado o error de dominio."""
    try:
        resultado = analizar_independencia(capturar_independencia(vectores))
        resultado["etiquetas"] = list(vectores)
        return json.dumps(resultado, cls=CodificadorMatriz, ensure_ascii=False)
    except ValueError as error:
        return json.dumps({"estado": "ERROR", "mensaje": str(error)}, ensure_ascii=False)
