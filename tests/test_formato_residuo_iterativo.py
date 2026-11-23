"""Explicaciones exactas de residuos que exceden el límite decimal de conversión de enteros."""
from collections.abc import Callable
from decimal import localcontext
from fractions import Fraction
import sys

import pytest

from src.backend.resolutores.sistemas_lineales.gauss_seidel import (
    ResultadoGaussSeidel, resolver_gauss_seidel_desde_captura,
)
from src.backend.resolutores.sistemas_lineales.iterativos.contrato_iterativo import (
    CodigoIterativo, ResultadoIterativo,
)
from src.backend.resolutores.sistemas_lineales.iterativos.formato_iterativo import (
    formatear_racional_exacto,
)
from src.backend.resolutores.sistemas_lineales.jacobi.contrato_jacobi import ResultadoJacobi
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import resolver_jacobi_desde_captura

_FRACCION_GRANDE = Fraction(10 ** 5000 + 1, 10 ** 5000 + 3)
_TEXTO_GRANDE = "1" + "0" * 4999 + "1/1" + "0" * 4999 + "3"


@pytest.mark.parametrize("valor,texto", [
    (Fraction(0), "0"), (Fraction(7), "7"),
    (Fraction(-2, 3), "-2/3"), (Fraction(1, 10), "1/10"),
])
def test_el_formato_conserva_las_fracciones_habituales(valor: Fraction, texto: str) -> None:
    """El formato mantiene enteros, signos y fracciones sin redondearlos."""
    assert formatear_racional_exacto(valor) == texto


def test_los_digitos_se_conservan_sin_alterar_la_proteccion_global() -> None:
    """Una fracción de dos enteros de 5001 dígitos se representa completa."""
    limite = sys.get_int_max_str_digits()

    assert formatear_racional_exacto(_FRACCION_GRANDE) == _TEXTO_GRANDE
    assert sys.get_int_max_str_digits() == limite


def test_la_precision_decimal_del_contexto_no_redondea_el_texto() -> None:
    """La conversión de cada entero es exacta aunque la precisión del contexto sea pequeña."""
    with localcontext() as contexto:
        contexto.prec = 3
        assert formatear_racional_exacto(Fraction(123456789, 1000000007)) == "123456789/1000000007"


@pytest.mark.parametrize("clase", [ResultadoGaussSeidel, ResultadoJacobi])
@pytest.mark.parametrize("codigo", [
    "TOLERANCIA_ALCANZADA", "MAXIMO_ITERACIONES", "LIMITE_ARITMETICO",
])
def test_las_explicaciones_incluyen_el_residuo_grande_completo(
    clase: type[ResultadoIterativo], codigo: CodigoIterativo,
) -> None:
    """Las tres salidas con norma positiva presentan el racional completo sin fallar."""
    resultado = clase(
        codigo=codigo, aproximacion=(Fraction(0),),
        residuo=(_FRACCION_GRANDE,), norma_residuo=_FRACCION_GRANDE,
    )

    assert _TEXTO_GRANDE in resultado.explicacion


@pytest.mark.parametrize("resolver", [
    resolver_gauss_seidel_desde_captura, resolver_jacobi_desde_captura,
])
def test_un_sistema_valido_explicita_su_residuo_de_miles_de_digitos(
    resolver: Callable[[object], ResultadoIterativo],
) -> None:
    """Cuatro productos de racionales válidos producen una norma con denominador de 15869 bits."""
    coeficientes = [Fraction(1, 2 ** 2000), Fraction(1, 3 ** 1250),
                    Fraction(1, 5 ** 850), Fraction(1, 7 ** 700)]
    inicio = [Fraction(1, 11 ** 570), Fraction(1, 13 ** 540),
              Fraction(1, 17 ** 490), Fraction(1, 19 ** 465)]
    matriz = [coeficientes] + [[int(fila == columna) for columna in range(4)]
                              for fila in range(1, 4)]
    resultado = resolver({
        "matriz_a": matriz, "vector_b": [0, *inicio[1:]], "vector_inicial": inicio,
        "tolerancia": "1/100", "maximo_iteraciones": 1,
    })

    assert resultado.codigo == "TOLERANCIA_ALCANZADA"
    assert resultado.iteraciones_realizadas == 0
    assert resultado.norma_residuo is not None
    assert resultado.norma_residuo.denominator.bit_length() == 15869
    assert len(resultado.explicacion) > 4300
    assert "cumple la tolerancia" in resultado.explicacion
