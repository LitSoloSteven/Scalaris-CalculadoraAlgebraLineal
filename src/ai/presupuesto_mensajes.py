"""Límite compartido para preguntas y mensajes retenidos de Glosa."""
from src.ai.constantes import MAXIMO_CARACTERES_MENSAJE


def validar_longitud_mensaje(texto: str) -> None:
    """Rechaza con ValueError un mensaje excesivo, sin modificar su contenido."""
    if not isinstance(texto, str):
        raise ValueError("El mensaje debe ser texto. Escribe tu pregunta y vuelve a enviarla.")
    if len(texto) > MAXIMO_CARACTERES_MENSAJE:
        raise ValueError(
            f"El mensaje supera {MAXIMO_CARACTERES_MENSAJE} caracteres. "
            "Acorta el texto y vuelve a enviarlo."
        )
