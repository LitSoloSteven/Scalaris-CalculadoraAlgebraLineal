"""Datos de entrada y salida del método de Gauss-Seidel para sistemas lineales."""
from dataclasses import dataclass

from ..iterativos import contrato_iterativo as comun

EscalarGaussSeidel = comun.EscalarIterativo
FilaCapturaGaussSeidel = comun.FilaCapturaIterativa
MatrizCrudaGaussSeidel = comun.MatrizCrudaIterativa
VectorGaussSeidel = comun.VectorIterativo
CodigoGaussSeidel = comun.CodigoIterativo
CampoGaussSeidel = comun.CampoIterativo


@dataclass(frozen=True, kw_only=True)
class EntradaGaussSeidel(comun.EntradaIterativa):
    """Recibe la cuadrícula original de coeficientes y admite texto racional en todos los escalares.
    La tolerancia positiva acota la norma infinito de b - A·x. El máximo cuenta barridos completos."""


@dataclass(frozen=True, kw_only=True)
class DiagnosticoGaussSeidel(comun.DiagnosticoIterativo):
    """Mensaje en español con campo y coordenadas desde 1 cuando se conocen.
    En un vector, la fila identifica la componente. La columna se usa en la matriz."""


@dataclass(frozen=True, kw_only=True)
class PasoGaussSeidel(comun.PasoIterativo):
    """Barrido completo con índice desde 1, vectores y normas infinito exactas.
    El vector nuevo se construye en orden y la traza conserva ambos vectores del barrido."""


@dataclass(frozen=True, kw_only=True)
class ResultadoGaussSeidel(comun.ResultadoIterativo):
    """Causa de parada y traza inmutable; solo SOLUCION_EXACTA y TOLERANCIA_ALCANZADA certifican.
    La aproximación y el residuo b - A·x son None hasta comprobar un vector completo."""
