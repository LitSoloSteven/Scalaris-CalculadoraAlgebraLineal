"""Delegación de cargas de combinación lineal al dominio geométrico."""
from src.backend.geometria.escena_combinacion import preparar_escena_combinacion
from src.frontend.controladores.geometria.carga import procesar_carga


def procesar_combinacion(carga_json: str) -> dict:
    """Valida objetivo y vectores del JSON y devuelve su escena serializable."""
    return procesar_carga(carga_json, {"objetivo", "vectores"}, preparar_escena_combinacion)
