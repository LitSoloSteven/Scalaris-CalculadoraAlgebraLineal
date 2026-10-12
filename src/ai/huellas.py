"""Huellas deterministas para detectar cambios en entradas del contexto matemático."""
import hashlib
import json
from typing import Any


def _normalizar_para_huella(objeto: Any) -> Any:
    if isinstance(objeto, dict):
        return {str(clave): _normalizar_para_huella(valor) for clave, valor in objeto.items()}
    if isinstance(objeto, (list, tuple)):
        return [_normalizar_para_huella(elemento) for elemento in objeto]
    return objeto


def calcular_huella(objeto: Any) -> str:
    """Devuelve el hash SHA-1 de la entrada normalizada con claves ordenadas."""
    serializado = json.dumps(_normalizar_para_huella(objeto), sort_keys=True, default=str)
    return hashlib.sha1(serializado.encode("utf-8")).hexdigest()


def esta_desactualizado(entrada_actual: Any, huella_resultado: str | None) -> bool:
    """Indica si la entrada difiere de la huella previa; sin huella devuelve falso."""
    if huella_resultado is None:
        return False
    return calcular_huella(entrada_actual) != huella_resultado
