"""Datos de entrada y salida del método de Gauss-Seidel para sistemas lineales."""
from dataclasses import dataclass

from ..iterativos.contrato_iterativo import (
    CampoIterativo, CodigoIterativo, DiagnosticoIterativo, EntradaIterativa,
    EscalarIterativo, FilaCapturaIterativa, MatrizCrudaIterativa, PasoIterativo,
    ResultadoIterativo, VectorIterativo,
)

EscalarGaussSeidel = EscalarIterativo
FilaCapturaGaussSeidel = FilaCapturaIterativa
MatrizCrudaGaussSeidel = MatrizCrudaIterativa
VectorGaussSeidel = VectorIterativo
CodigoGaussSeidel = CodigoIterativo
CampoGaussSeidel = CampoIterativo


@dataclass(frozen=True, kw_only=True)
class EntradaGaussSeidel(EntradaIterativa):
    """Recibe la cuadrícula original de coeficientes y admite texto racional en todos los escalares.
    La tolerancia positiva acota la norma infinito de b - A·x. El máximo cuenta barridos completos."""


@dataclass(frozen=True, kw_only=True)
class DiagnosticoGaussSeidel(DiagnosticoIterativo):
    """Mensaje en español con campo y coordenadas desde 1 cuando se conocen.
    En un vector, la fila identifica la componente. La columna se usa en la matriz."""


@dataclass(frozen=True, kw_only=True)
class PasoGaussSeidel(PasoIterativo):
    """Barrido completo con índice desde 1, vectores y normas infinito exactas.
    El vector nuevo se construye en orden y la traza conserva ambos vectores del barrido."""


@dataclass(frozen=True, kw_only=True)
class ResultadoGaussSeidel(ResultadoIterativo):
    """Causa de parada y traza inmutable; solo SOLUCION_EXACTA y TOLERANCIA_ALCANZADA certifican.
    La aproximación y el residuo b - A·x son None hasta comprobar un vector completo."""
