"""Aritmética exacta y presupuesto de crecimiento para el método de Jacobi."""
from ..iterativos.aritmetica_iterativa import (
    ConfiguracionAritmetica,
    LimiteAritmeticoIterativo as LimiteAritmeticoJacobi,
    PresupuestoAritmetico as _PresupuestoAritmetico,
    norma_infinito,
    producto_fila,
    producto_fila_mixto,
    producto_fila_sin_diagonal,
    residuo_sistema,
)
from .limites_jacobi import (
    MAXIMO_BITS_ACUMULACION_JACOBI,
    MAXIMO_BITS_CALCULO_JACOBI,
    MAXIMO_BITS_CAMBIO_JACOBI,
    MAXIMO_BITS_ENTRADA_JACOBI,
    MAXIMO_OPERACIONES_JACOBI,
)


class PresupuestoAritmetico(_PresupuestoAritmetico):
    """Presupuesto de Jacobi con los topes vigentes del módulo."""

    def __init__(self, operaciones: int | None = None) -> None:
        """Inicia el contador con el tope recibido o el límite documentado de Jacobi."""
        super().__init__(
            ConfiguracionAritmetica(
                maximo_operaciones=MAXIMO_OPERACIONES_JACOBI,
                maximo_bits_entrada=MAXIMO_BITS_ENTRADA_JACOBI,
                maximo_bits_calculo=MAXIMO_BITS_CALCULO_JACOBI,
                maximo_bits_cambio=MAXIMO_BITS_CAMBIO_JACOBI,
                maximo_bits_acumulacion=MAXIMO_BITS_ACUMULACION_JACOBI,
            ),
            operaciones,
        )


__all__ = [
    "LimiteAritmeticoJacobi",
    "PresupuestoAritmetico",
    "norma_infinito",
    "producto_fila",
    "producto_fila_mixto",
    "producto_fila_sin_diagonal",
    "residuo_sistema",
]
