"""Caché acotada de respuestas, aislada por instancia y contenido enviado."""
import hashlib
import json
import threading

from src.ai.constantes import CAPACIDAD_MAXIMA_CACHE, TIEMPO_VIDA_CACHE_SEGUNDOS
from src.ai.respuestas import ResultadoIA

_bloqueo_cache = threading.Lock()
_cache_respuestas: dict[str, tuple[ResultadoIA, float]] = {}


def calcular_hash_cache(mensajes: list, modelos: list[str], espacio_cliente: str) -> str:
    """Identifica los mensajes y modelos efectivos dentro del espacio del cliente."""
    datos = json.dumps([espacio_cliente, modelos, mensajes], ensure_ascii=False)
    return hashlib.sha256(datos.encode("utf-8")).hexdigest()


def leer_cache(clave_cache: str, ahora: float) -> ResultadoIA | None:
    """Retira respuestas vencidas y devuelve una copia marcada como almacenada."""
    with _bloqueo_cache:
        expiradas = [
            clave for clave, entrada in _cache_respuestas.items()
            if ahora - entrada[1] > TIEMPO_VIDA_CACHE_SEGUNDOS
        ]
        for clave in expiradas:
            del _cache_respuestas[clave]
        if clave_cache in _cache_respuestas:
            resultado, _ = _cache_respuestas[clave_cache]
            return ResultadoIA(True, resultado.texto, modelo=resultado.modelo, desde_cache=True)
    return None


def guardar_en_cache(clave_cache: str, resultado: ResultadoIA, ahora: float) -> None:
    """Almacena una respuesta desalojando la entrada con fecha más antigua."""
    with _bloqueo_cache:
        if len(_cache_respuestas) >= CAPACIDAD_MAXIMA_CACHE:
            mas_antiguo = min(_cache_respuestas, key=lambda clave: _cache_respuestas[clave][1])
            del _cache_respuestas[mas_antiguo]
        _cache_respuestas[clave_cache] = (resultado, ahora)
