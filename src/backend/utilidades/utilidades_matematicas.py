"""Operaciones aritméticas sobre enteros y reducción de filas."""

from typing import List


def mcd(primer_numero: int, segundo_numero: int) -> int:
    """Calcula el Máximo Común Divisor mediante el algoritmo de Euclides."""
    primer_numero, segundo_numero = abs(primer_numero), abs(segundo_numero)
    while segundo_numero:
        primer_numero, segundo_numero = segundo_numero, primer_numero % segundo_numero
    return primer_numero


def mcm(primer_numero: int, segundo_numero: int) -> int:
    """Calcula el Mínimo Común Múltiplo de dos números enteros."""
    if primer_numero == 0 or segundo_numero == 0:
        return 0
    return abs(primer_numero * segundo_numero) // mcd(primer_numero, segundo_numero)


def mcd_lista(numeros: List[int]) -> int:
    """Calcula el MCD de una secuencia de números enteros no nulos."""
    numeros_no_cero = [abs(numero) for numero in numeros if numero != 0]
    if not numeros_no_cero:
        return 1
    resultado = numeros_no_cero[0]
    for numero in numeros_no_cero[1:]:
        resultado = mcd(resultado, numero)
    return resultado


def simplificar_fila(fila: List[int]) -> List[int]:
    """Reduce los coeficientes de una fila dividiéndolos por su MCD."""
    factor = mcd_lista(fila)
    if factor <= 1:
        return fila
    return [elem // factor for elem in fila]
