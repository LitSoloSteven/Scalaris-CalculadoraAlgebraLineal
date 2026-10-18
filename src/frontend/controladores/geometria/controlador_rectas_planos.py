"""Delegación de cargas de sistemas al dominio geométrico."""
from src.backend.geometria.escena_sistema import preparar_escena_sistema
from src.frontend.controladores.geometria.carga import procesar_carga


def procesar_rectas_planos(carga_json: str) -> dict:
    """Valida la carga JSON de A y b y devuelve su representación serializable."""
    return procesar_carga(carga_json, {"matriz_a", "vector_b"}, preparar_escena_sistema)
