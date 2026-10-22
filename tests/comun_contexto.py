"""Comprobaciones comunes del presupuesto y la señal de truncado del contexto."""
from src.ai.contexto import serializar_contexto
from src.ai.constantes import MAXIMO_CARACTERES_CONTEXTO


def comprobar_contexto_truncado(contexto, extraer_json):
    """Serializa y exige el presupuesto, el objeto JSON y su marca de truncado."""
    serializado = serializar_contexto(contexto)
    assert len(serializado) <= MAXIMO_CARACTERES_CONTEXTO
    datos = extraer_json(serializado)
    assert isinstance(datos, dict)
    assert datos.get('metadatos', {}).get('truncado') is True
    return serializado, datos
