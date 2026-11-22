"""Datos comunes de entrada y salida de los métodos iterativos."""
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

EscalarIterativo = Fraction | int | str
FilaCapturaIterativa = list[EscalarIterativo] | tuple[EscalarIterativo, ...]
MatrizCrudaIterativa = list[FilaCapturaIterativa] | tuple[FilaCapturaIterativa, ...]
VectorIterativo = tuple[Fraction, ...]
CodigoIterativo = Literal[
    "SOLUCION_EXACTA",
    "TOLERANCIA_ALCANZADA",
    "MAXIMO_ITERACIONES",
    "LIMITE_ARITMETICO",
    "DIAGONAL_NULA",
    "ENTRADA_INVALIDA",
]
CampoIterativo = Literal[
    "entrada", "matriz_a", "vector_b", "vector_inicial", "tolerancia", "maximo_iteraciones",
]


@dataclass(frozen=True, kw_only=True)
class EntradaIterativa:
    """Recibe la cuadrícula original de coeficientes y admite texto racional en todos los escalares.
    La tolerancia positiva acota la norma infinito de b - A·x. El máximo cuenta barridos completos."""

    matriz_a: MatrizCrudaIterativa
    vector_b: tuple[EscalarIterativo, ...]
    vector_inicial: tuple[EscalarIterativo, ...]
    tolerancia: EscalarIterativo
    maximo_iteraciones: int


@dataclass(frozen=True, kw_only=True)
class DiagnosticoIterativo:
    """Mensaje en español con campo y coordenadas desde 1 cuando se conocen.
    En un vector, la fila identifica la componente. La columna se usa en la matriz."""

    mensaje: str
    campo: CampoIterativo | None = None
    fila: int | None = None
    columna: int | None = None


@dataclass(frozen=True, kw_only=True)
class PasoIterativo:
    """Barrido completo con índice desde 1, vectores y normas infinito exactas.
    La traza conserva el vector previo y el actualizado para reproducir cada sustitución."""

    indice: int
    vector_anterior: VectorIterativo
    vector_nuevo: VectorIterativo
    norma_cambio: Fraction
    norma_residuo: Fraction


@dataclass(frozen=True, kw_only=True)
class ResultadoIterativo:
    """Causa de parada y traza inmutable; solo SOLUCION_EXACTA y TOLERANCIA_ALCANZADA certifican.
    La aproximación y el residuo b - A·x son None hasta comprobar un vector completo."""

    codigo: CodigoIterativo
    aproximacion: VectorIterativo | None = None
    residuo: VectorIterativo | None = None
    norma_residuo: Fraction | None = None
    dominancia_estricta: bool | None = None
    pasos: tuple[PasoIterativo, ...] = ()
    diagnostico: DiagnosticoIterativo | None = None

    @property
    def iteraciones_realizadas(self) -> int:
        """Devuelve el número de barridos completos en la traza."""
        return len(self.pasos)
