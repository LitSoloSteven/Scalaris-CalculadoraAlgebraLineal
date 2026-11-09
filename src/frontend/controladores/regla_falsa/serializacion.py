"""Serialización del resultado de regla falsa sin alterar su contrato."""
import json
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_regla_falsa import ResultadoReglaFalsa


def serializar_resultado(resultado: ResultadoReglaFalsa) -> dict:
    """Devuelve una copia serializable y finita del resultado; lanza ValueError si no lo es."""
    if not isinstance(resultado, ResultadoReglaFalsa):
        raise ValueError("El resultado no cumple el contrato de regla falsa.")
    respuesta = asdict(resultado)
    try:
        json.dumps(respuesta, allow_nan=False)
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise ValueError("El resultado no se puede representar. Revisa la magnitud de los valores.") from error
    return respuesta
