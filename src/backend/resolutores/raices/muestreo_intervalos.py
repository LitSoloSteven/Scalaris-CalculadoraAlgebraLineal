"""Malla por índice con presupuesto comprobado antes de reservar posiciones."""
from fractions import Fraction

from .contrato_exploracion import EntradaExploracion, validar_exploracion
from .limites_exploracion import MAXIMO_EVALUACIONES_EXPLORACION


def generar_posiciones(entrada: EntradaExploracion) -> tuple[float, ...]:
    """Incluye ambos extremos; lanza ValueError por presupuesto o redondeo sin avance."""
    entrada = validar_exploracion(entrada)
    minimo = Fraction(entrada.x_min)
    maximo = Fraction(entrada.x_max)
    paso = Fraction(entrada.paso)
    cociente = (maximo - minimo) / paso
    segmentos = -(-cociente.numerator // cociente.denominator)
    if segmentos + 1 > MAXIMO_EVALUACIONES_EXPLORACION:
        raise ValueError("El paso exige demasiadas evaluaciones; aumenta el paso o reduce el rango.")
    posiciones = tuple(float(minimo + indice * paso) for indice in range(segmentos))
    posiciones += (entrada.x_max,)
    if any(izquierda >= derecha for izquierda, derecha in zip(posiciones, posiciones[1:])):
        raise ValueError("El paso no permite avanzar con la precisión disponible; aumenta el paso.")
    return posiciones
