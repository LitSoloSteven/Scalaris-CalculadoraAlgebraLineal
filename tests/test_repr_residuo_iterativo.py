"""Representación de depuración de resultados y pasos con residuos grandes."""
from collections.abc import Callable
from dataclasses import asdict
from fractions import Fraction
from sys import get_int_max_str_digits

import pytest

from src.backend.resolutores.sistemas_lineales.gauss_seidel import (
    resolver_gauss_seidel_desde_captura,
)
from src.backend.resolutores.sistemas_lineales.iterativos.contrato_iterativo import ResultadoIterativo
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import resolver_jacobi_desde_captura


@pytest.mark.parametrize("resolver", [
    resolver_gauss_seidel_desde_captura, resolver_jacobi_desde_captura,
])
def test_repr_admite_un_barrido_con_residuo_de_miles_de_digitos(
    resolver: Callable[[object], ResultadoIterativo],
) -> None:
    """Un barrido verificable conserva sus residuos exactos y se puede registrar."""
    coeficientes = (
        Fraction(1, 2 ** 2000), Fraction(1, 3 ** 1250),
        Fraction(1, 5 ** 850), Fraction(1, 7 ** 700),
    )
    independientes = (
        Fraction(1, 11 ** 570), Fraction(1, 13 ** 540),
        Fraction(1, 17 ** 490), Fraction(1, 19 ** 465),
    )
    matriz = [(1, *coeficientes)] + [
        tuple(int(fila == columna) for columna in range(5)) for fila in range(1, 5)
    ]
    resultado = resolver({
        "matriz_a": matriz, "vector_b": (0, *independientes),
        "tolerancia": Fraction(1, 2 ** 3000), "maximo_iteraciones": 1,
    })
    assert resultado.codigo == "TOLERANCIA_ALCANZADA"
    paso, = resultado.pasos
    norma = sum((
        coeficiente * valor
        for coeficiente, valor in zip(coeficientes, independientes, strict=True)
    ), Fraction(0))
    assert norma.denominator.bit_length() == 15869

    limite = get_int_max_str_digits()
    texto_resultado = repr(resultado)
    texto_paso = repr(paso)
    assert "codigo='TOLERANCIA_ALCANZADA'" in texto_resultado
    assert "indice=1" in texto_paso
    assert "residuo=" not in texto_resultado + texto_paso
    assert get_int_max_str_digits() == limite

    serializado = asdict(resultado)
    assert serializado["residuo"] == (-norma, 0, 0, 0, 0)
    assert serializado["norma_residuo"] == norma
    assert serializado["pasos"][0]["norma_residuo"] == norma
    assert "cumple la tolerancia" in resultado.explicacion
