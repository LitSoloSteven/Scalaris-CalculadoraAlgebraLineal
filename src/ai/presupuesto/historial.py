"""Contrato interno único del historial compartido por Glosa y el cliente de IA."""
from typing import Any
from src.ai.constantes import MAXIMO_CARACTERES_MENSAJE


CAMPOS_MENSAJE = frozenset({
    "texto", "enviado", "error", "reintentar", "almacenable_en_cache", "mas_simple", "animar",
})


def es_contrato_historial(mensaje: Any) -> bool:
    """Indica si el mensaje usa solo campos internos y un remitente booleano."""
    return (isinstance(mensaje, dict) and set(mensaje).issubset(CAMPOS_MENSAJE)
            and isinstance(mensaje.get("enviado", False), bool))


def limpiar_historial_almacenado(historial: Any, limite: int) -> list[dict[str, Any]]:
    """Copia los mensajes canónicos textuales más recientes; descarta datos ajenos."""
    if not isinstance(historial, list):
        return []
    mensajes = [dict(mensaje) for mensaje in historial
                if es_contrato_historial(mensaje) and isinstance(mensaje.get("texto"), str)
                and len(mensaje["texto"]) <= MAXIMO_CARACTERES_MENSAJE]
    return mensajes[-limite:]
