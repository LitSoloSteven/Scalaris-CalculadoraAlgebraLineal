"""Catálogo local de ejemplos didácticos fijos para la portada."""
from dataclasses import dataclass
from functools import cache
from pathlib import Path
import re

_CARPETA_PLANTILLAS = Path(__file__).resolve().parents[2] / "recursos" / "plantillas" / "inicio"
_PATRON_BLOQUE = re.compile(r'<template\s+data-ejemplo="([^"]+)">\s*(.*?)\s*</template>', re.DOTALL)


@dataclass(frozen=True)
class EjemploInicio:
    """Metadatos y etapas didácticas locales asociadas a un acceso."""

    clave: str
    operacion: str
    etiqueta_operacion: str
    mensaje: str
    etapas: str


_EJEMPLOS_PORTADA: dict[str, tuple[str, str, str, str]] = {
    "sistemas": (
        "F₂ ← F₂ − F₁",
        "Resta la primera fila de la segunda",
        "Se eliminó x de la segunda fila.",
        "ejemplos_inicio_algebra.html",
    ),
    "metodos_iterativos": (
        "x⁽⁰⁾ → x⁽¹⁾",
        "Primer barrido de Jacobi desde el vector inicial",
        "Cada componente del primer barrido se obtuvo a partir del vector inicial.",
        "ejemplos_inicio_algebra.html",
    ),
    "leontief": (
        "C = diag(1/2, 1/4)",
        "Matriz tecnológica diagonal con un medio y un cuarto",
        "La demanda de diez y seis requiere producción de veinte y ocho.",
        "ejemplos_inicio_algebra.html",
    ),
    "matrices": (
        "(AB)₁₁ = 1·2 + 2·1",
        "Producto de la primera fila por la primera columna",
        "La primera entrada de AB es cuatro.",
        "ejemplos_inicio_algebra.html",
    ),
    "inversa": (
        "A = diag(2, 3)",
        "Matriz diagonal de dos por dos",
        "Los bloques pasan de A e I a I y A inversa.",
        "ejemplos_inicio_algebra.html",
    ),
    "factorizacion_lu": (
        "PA = LU",
        "Factorización P A igual a L U con pivoteo parcial",
        "Se permutaron las filas para formar los factores L y U.",
        "ejemplos_inicio_algebra.html",
    ),
    "determinantes": (
        "det = 2 × 1,5 = 3",
        "Determinante igual a base dos por altura uno coma cinco, igual a tres",
        "El cuadrado de área uno pasa a paralelogramo de área tres.",
        "ejemplos_inicio_geometria.html",
    ),
    "vectores": (
        "v = 2u",
        "Vector v igual a dos por u",
        "El vector v duplica la longitud de u en la misma dirección.",
        "ejemplos_inicio_geometria.html",
    ),
    "transformaciones": (
        "T(x, y) = (x + y, y)",
        "Transformación lineal de x coma y en x más y coma y",
        "La transformación inclina el cuadrado en el eje horizontal.",
        "ejemplos_inicio_geometria.html",
    ),
    "vis:rectas-planos": (
        "y = 3 − x, y = x − 1",
        "Rectas y igual a tres menos x e y igual a x menos uno",
        "Las dos rectas se cruzan en el punto (2, 1).",
        "ejemplos_inicio_geometria.html",
    ),
    "vis:vectores": (
        "(2, 1) + (1, 2)",
        "Suma de los vectores dos coma uno y uno coma dos",
        "El método punta-cola une ambos vectores hasta (3, 3).",
        "ejemplos_inicio_geometria.html",
    ),
    "vis:combinacion": (
        "2e₁ + 3e₂ = (2, 3)",
        "Dos por e sub uno más tres por e sub dos igual a dos coma tres",
        "Dos veces e uno más tres veces e dos forman el vector (2, 3).",
        "ejemplos_inicio_geometria.html",
    ),
    "metodos_cerrados": (
        "f(x) = x² − 2",
        "Función x al cuadrado menos dos",
        "El extremo superior se reduce de dos a uno coma cinco.",
        "ejemplos_inicio_numericos.html",
    ),
    "metodos_abiertos": (
        "x₁ = x₀ − f(x₀)/f'(x₀)",
        "Fórmula de Newton-Raphson",
        "La tangente en dos cruza el eje en x sub uno igual a uno coma cinco.",
        "ejemplos_inicio_numericos.html",
    ),
    "bases": (
        "1010₂ → 10₁₀",
        "Uno cero uno cero en base dos a diez en base diez",
        "Los pesos ocho y dos suman diez en base diez.",
        "ejemplos_inicio_numericos.html",
    ),
    "romanos": (
        "XIV + IX = XXIII",
        "Catorce más nueve igual a veintitrés",
        "Catorce más nueve suman veintitrés en numeración romana.",
        "ejemplos_inicio_numericos.html",
    ),
}

CLAVES_EJEMPLOS: frozenset[str] = frozenset(_EJEMPLOS_PORTADA)


@cache
def _etapas_archivo(nombre_archivo: str) -> dict[str, str]:
    """Extrae e indexa los bloques locales de ejemplo de una plantilla por familia."""
    contenido = (_CARPETA_PLANTILLAS / nombre_archivo).read_text(encoding="utf-8")
    return {clave: fragmento for clave, fragmento in _PATRON_BLOQUE.findall(contenido)}


def obtener_ejemplo(clave: str) -> EjemploInicio:
    """Devuelve el ejemplo didáctico fijo del acceso o el respaldo de sistemas."""
    clave_efectiva = clave if clave in _EJEMPLOS_PORTADA else "sistemas"
    operacion, etiqueta_operacion, mensaje, plantilla = _EJEMPLOS_PORTADA[clave_efectiva]
    etapas = _etapas_archivo(plantilla)[clave_efectiva]
    return EjemploInicio(
        clave=clave_efectiva,
        operacion=operacion,
        etiqueta_operacion=etiqueta_operacion,
        mensaje=mensaje,
        etapas=etapas,
    )
