"""Delegación de cargas vectoriales al dominio geométrico."""
from src.backend.geometria.escenas.escena_vectores import preparar_escena_vectores
from src.frontend.controladores.geometria.base.carga import procesar_carga


def procesar_vectores(carga_json: str) -> dict:
    """Valida la carga JSON y devuelve la escena vectorial serializable del backend."""
    return procesar_carga(carga_json, {"vectores"}, preparar_escena_vectores)
