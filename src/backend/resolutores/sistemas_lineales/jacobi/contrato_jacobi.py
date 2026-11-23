"""Datos de entrada y salida del método de Jacobi para sistemas lineales."""
from dataclasses import dataclass

from ..iterativos.contrato_iterativo import (
    CampoIterativo, CodigoIterativo, DiagnosticoIterativo, EntradaIterativa,
    EscalarIterativo, FilaCapturaIterativa, MatrizCrudaIterativa, PasoIterativo,
    ResultadoIterativo, VectorIterativo,
)

EscalarJacobi = EscalarIterativo
FilaCapturaJacobi = FilaCapturaIterativa
MatrizCrudaJacobi = MatrizCrudaIterativa
VectorJacobi = VectorIterativo
CodigoJacobi = CodigoIterativo
CampoJacobi = CampoIterativo


@dataclass(frozen=True, kw_only=True)
class EntradaJacobi(EntradaIterativa):
    """Recibe la cuadrícula original de coeficientes y admite texto racional en todos los escalares.
    La tolerancia positiva acota la norma infinito de b - A·x. El máximo cuenta actualizaciones completas."""


@dataclass(frozen=True, kw_only=True)
class DiagnosticoJacobi(DiagnosticoIterativo):
    """Mensaje en español con campo y coordenadas desde 1 cuando se conocen.
    En un vector, la fila identifica la componente. La columna se usa en la matriz."""


@dataclass(frozen=True, kw_only=True)
class PasoJacobi(PasoIterativo):
    """Actualización completa con índice desde 1, vectores y normas infinito exactas.
    Todas las componentes parten del vector anterior; la norma del cambio usa un límite derivado."""


@dataclass(frozen=True, kw_only=True)
class ResultadoJacobi(ResultadoIterativo):
    """Causa de parada y traza inmutable; solo SOLUCION_EXACTA y TOLERANCIA_ALCANZADA certifican.
    La aproximación y el residuo b - A·x son None hasta comprobar un vector completo."""
