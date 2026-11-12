"""Ejercicios identificados como ejemplos con preferencias matemáticas explícitas."""
from .estado_captura import PREFERENCIAS_INICIALES


def _ejercicio(expresion: str, inferior: str, superior: str) -> dict:
    return {**PREFERENCIAS_INICIALES, "expresion": expresion,
            "extremo_izquierdo": inferior, "extremo_derecho": superior}


EJEMPLOS = (
    ("Raíz de 2", _ejercicio("x^2 - 2", "1", "2")),
    ("Intervalo invertido", _ejercicio("x^2 - 2", "2", "1")),
    ("Raíz cero en un extremo", _ejercicio("x", "0", "2")),
    ("Seno en grados", _ejercicio("2sin(x) - 1", "0", "60") | {"unidad_angular": "grados"}),
    ("Sin cambio de signo", _ejercicio("x^2 + 1", "-1", "1")),
    ("Una iteración", _ejercicio("x^2 - 2", "1", "2") | {"limite_iteraciones": "1"}),
)
