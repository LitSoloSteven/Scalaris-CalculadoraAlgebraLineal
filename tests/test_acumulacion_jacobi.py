"""Regresiones de cancelación exacta en los productos escalares de Jacobi."""
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.contrato_jacobi import EntradaJacobi
from src.backend.resolutores.sistemas_lineales.jacobi import (
    resolver_jacobi, resolver_jacobi_desde_captura,
)
from src.backend.resolutores.sistemas_lineales.limites_jacobi import MAXIMO_BITS_CALCULO_JACOBI


@pytest.mark.parametrize("cancelar_primero", [False, True])
@pytest.mark.parametrize("pasos_esperados", [0, 1])
def test_cancelacion_entera_respeta_la_solucion_exacta(
    cancelar_primero: bool, pasos_esperados: int,
) -> None:
    """El orden de los términos conserva el resultado al verificar o calcular un paso."""
    grande = 2 ** (MAXIMO_BITS_CALCULO_JACOBI - 1)
    fuera_diagonal = (grande, -grande, grande) if cancelar_primero else (grande, grande, -grande)
    matriz = Matriz(4, 4, [
        [1, *fuera_diagonal], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1],
    ])
    resultado = resolver_jacobi(EntradaJacobi(
        matriz_a=matriz, vector_b=(grande + pasos_esperados, 1, 1, 1),
        vector_inicial=(0, 1, 1, 1), tolerancia=Fraction(1, 100), maximo_iteraciones=1,
    ))

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.iteraciones_realizadas == pasos_esperados
    assert resultado.aproximacion == (pasos_esperados, 1, 1, 1)
    assert resultado.residuo == (0, 0, 0, 0)


@pytest.mark.parametrize("cancelar_primero", [False, True])
def test_cancelacion_de_fracciones_capturadas(cancelar_primero: bool) -> None:
    """El residuo cero se reconoce con denominadores parciales de más de 4096 bits."""
    denominadores = tuple(primo ** (720 // primo.bit_length()) for primo in (2, 3, 5, 7, 11, 13, 17, 19))
    mitad = len(denominadores) // 2
    positivos = [f"1/{denominador}" for denominador in denominadores[:mitad]]
    coeficientes = positivos + [f"-{valor}" for valor in positivos]
    iniciales = [f"1/{denominador}" for denominador in denominadores[mitad:]] * 2
    orden = len(coeficientes)
    indices = (0, 4, 1, 5, 2, 6, 3, 7) if cancelar_primero else tuple(range(orden))
    inicio = [iniciales[indice] for indice in indices]
    matriz = [[coeficientes[indice] for indice in indices]] + [
        [int(fila == columna) for columna in range(orden)] for fila in range(1, orden)
    ]
    parcial = sum(Fraction(coeficiente) * Fraction(inicial)
                  for coeficiente, inicial in zip(positivos, iniciales))
    assert parcial.denominator.bit_length() > MAXIMO_BITS_CALCULO_JACOBI

    resultado = resolver_jacobi_desde_captura({
        "matriz_a": matriz, "vector_b": [0, *inicio[1:]], "vector_inicial": inicio,
        "tolerancia": "1/100", "maximo_iteraciones": 1,
    })

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.iteraciones_realizadas == 0
    assert resultado.residuo == (0,) * orden
