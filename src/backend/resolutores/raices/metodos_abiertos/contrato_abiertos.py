"""Contrato de entrada y salida de los métodos abiertos de resolución de raíces."""
from dataclasses import dataclass
from typing import Literal

MetodoAbierto = Literal["newton", "secante"]
EstadoAbierto = Literal[
    "EXITO",
    "LIMITE_ITERACIONES",
    "DERIVADA_NULA",
    "DENOMINADOR_NULO",
    "DIVERGENCIA",
    "ERROR",
]
CriterioParada = Literal["", "residuo", "cambio"]


@dataclass(frozen=True, kw_only=True)
class EntradaMetodoAbierto:
    """Expresión, puntos iniciales y límites validados para un método abierto."""

    metodo: MetodoAbierto
    expresion: str
    x0: float
    x1: float | None = None
    tolerancia: float = 1e-6
    limite_iteraciones: int = 100


@dataclass(frozen=True)
class IteracionMetodoAbierto:
    """Registro inmutable de una iteración con la aproximación siguiente ya evaluada."""

    i: int
    x_anterior: float | None
    f_x_anterior: float | None
    x_n: float
    f_x_n: float
    derivada: float | None
    x_siguiente: float | None
    f_x_siguiente: float | None
    residuo: float | None
    error_absoluto: float | None
    error_relativo_porcentual: float | None
    criterio: CriterioParada = ""


@dataclass(frozen=True)
class ResultadoMetodoAbierto:
    """Resultado completo del método con estado, raíz aproximada y trazabilidad."""

    metodo: MetodoAbierto
    entrada: EntradaMetodoAbierto | None = None
    estado: EstadoAbierto = "ERROR"
    mensaje: str = ""
    codigo_diagnostico: str = ""
    raiz: float | None = None
    residuo: float | None = None
    iteraciones: tuple[IteracionMetodoAbierto, ...] = ()
    iteraciones_totales: int = 0
    derivada_expresion: str | None = None
    advertencias: tuple[str, ...] = ()
    contexto_fallo: dict | None = None
