"""Aritmética exacta y presupuesto de crecimiento para el método de Jacobi."""
from fractions import Fraction

from .limites_jacobi import (
    MAXIMO_BITS_ACUMULACION_JACOBI, MAXIMO_BITS_CALCULO_JACOBI,
    MAXIMO_OPERACIONES_JACOBI, fraccion_admitida,
)


class LimiteAritmeticoJacobi(ArithmeticError):
    """Señala que el cálculo exacto superó el presupuesto configurado."""


class PresupuestoAritmetico:
    """Cuenta operaciones exactas y rechaza fracciones fuera del tamaño admitido."""

    def __init__(self, operaciones: int | None = None) -> None:
        """Inicia el contador con el tope recibido o el límite vigente del módulo."""
        self.restantes = MAXIMO_OPERACIONES_JACOBI if operaciones is None else operaciones

    def consumir(self, cantidad: int = 1) -> None:
        """Descuenta operaciones y lanza el límite cuando ya no quedan disponibles."""
        self.restantes -= cantidad
        if self.restantes < 0:
            raise LimiteAritmeticoJacobi(
                "El cálculo exacto superó el presupuesto de operaciones."
            )

    def registrar(
        self, valor: Fraction, maximo_bits: int = MAXIMO_BITS_CALCULO_JACOBI,
    ) -> Fraction:
        """Comprueba el tamaño de la fracción y la devuelve sin modificarla."""
        if not fraccion_admitida(valor, maximo_bits):
            raise LimiteAritmeticoJacobi(
                "El cálculo exacto superó el tamaño máximo de una fracción."
            )
        return valor


def producto_fila(
    fila: tuple[Fraction, ...],
    vector: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> Fraction:
    """Devuelve el producto escalar exacto de una fila y un vector de igual dimensión."""
    if len(fila) != len(vector):
        raise ValueError("La fila y el vector deben tener la misma dimensión.")
    total = Fraction(0)
    for coeficiente, componente in zip(fila, vector):
        presupuesto.consumir(2)
        total = presupuesto.registrar(total + coeficiente * componente, MAXIMO_BITS_ACUMULACION_JACOBI)
    return total


def producto_fila_sin_diagonal(
    fila: tuple[Fraction, ...],
    indice: int,
    vector: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> Fraction:
    """Suma los productos de una fila omitiendo el coeficiente diagonal."""
    if len(fila) != len(vector):
        raise ValueError("La fila y el vector deben tener la misma dimensión.")
    total = Fraction(0)
    for posicion, coeficiente in enumerate(fila):
        if posicion == indice:
            continue
        presupuesto.consumir(2)
        total = presupuesto.registrar(
            total + coeficiente * vector[posicion], MAXIMO_BITS_ACUMULACION_JACOBI,
        )
    return total


def residuo_sistema(
    matriz: tuple[tuple[Fraction, ...], ...],
    vector_b: tuple[Fraction, ...],
    vector: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> tuple[Fraction, ...]:
    """Devuelve b - A·x componente a componente; exige dimensiones coincidentes."""
    if len(matriz) != len(vector_b) or any(len(fila) != len(vector) for fila in matriz):
        raise ValueError("La matriz, b y la aproximación deben coincidir en dimensión.")
    residuo = []
    for termino, fila in zip(vector_b, matriz):
        producto = producto_fila(fila, vector, presupuesto)
        presupuesto.consumir()
        residuo.append(presupuesto.registrar(termino - producto))
    return tuple(residuo)


def norma_infinito(vector: tuple[Fraction, ...]) -> Fraction:
    """Devuelve el máximo de los valores absolutos de un vector no vacío."""
    return max(abs(componente) for componente in vector)
