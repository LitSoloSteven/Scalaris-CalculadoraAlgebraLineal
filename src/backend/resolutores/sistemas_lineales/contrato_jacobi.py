"""Datos de entrada y salida del método de Jacobi para sistemas lineales."""
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from src.backend.modelos.matriz import Matriz

EscalarJacobi = Fraction | int | str
VectorJacobi = tuple[Fraction, ...]
CodigoJacobi = Literal[
    "SOLUCION_EXACTA",
    "TOLERANCIA_ALCANZADA",
    "MAXIMO_ITERACIONES",
    "LIMITE_ARITMETICO",
    "DIAGONAL_NULA",
    "ENTRADA_INVALIDA",
]
CampoJacobi = Literal[
    "entrada", "matriz_a", "vector_b", "vector_inicial", "tolerancia", "maximo_iteraciones",
]


@dataclass(frozen=True, kw_only=True)
class EntradaJacobi:
    """Recibe una Matriz exacta desde su origen y admite texto racional en vectores y tolerancia.
    La tolerancia positiva acota la norma infinito de b - A·x. El máximo cuenta actualizaciones completas."""

    matriz_a: Matriz
    vector_b: tuple[EscalarJacobi, ...]
    vector_inicial: tuple[EscalarJacobi, ...]
    tolerancia: EscalarJacobi
    maximo_iteraciones: int


@dataclass(frozen=True, kw_only=True)
class DiagnosticoJacobi:
    """Mensaje en español con campo y coordenadas desde 1 cuando se conocen.
    En un vector, la fila identifica la componente. La columna se usa en la matriz."""

    mensaje: str
    campo: CampoJacobi | None = None
    fila: int | None = None
    columna: int | None = None


@dataclass(frozen=True, kw_only=True)
class PasoJacobi:
    """Actualización completa con índice desde 1, vectores y normas infinito exactas.
    Todas las componentes parten del vector anterior; la norma del cambio usa un límite derivado."""

    indice: int
    vector_anterior: VectorJacobi
    vector_nuevo: VectorJacobi
    norma_cambio: Fraction
    norma_residuo: Fraction


@dataclass(frozen=True, kw_only=True)
class ResultadoJacobi:
    """Causa de parada y traza inmutable; solo SOLUCION_EXACTA y TOLERANCIA_ALCANZADA certifican.
    La aproximación y el residuo b - A·x son None hasta comprobar un vector completo."""

    codigo: CodigoJacobi
    aproximacion: VectorJacobi | None = None
    residuo: VectorJacobi | None = None
    norma_residuo: Fraction | None = None
    dominancia_estricta: bool | None = None
    pasos: tuple[PasoJacobi, ...] = ()
    diagnostico: DiagnosticoJacobi | None = None

    @property
    def iteraciones_realizadas(self) -> int:
        """Devuelve el número de actualizaciones completas en la traza."""
        return len(self.pasos)
