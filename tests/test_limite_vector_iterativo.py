"""La cota propia del residuo no amplía las aproximaciones admitidas."""
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.gauss_seidel import resolver_gauss_seidel_desde_captura
from src.backend.resolutores.sistemas_lineales.iterativos.limites_iterativos import (
    MAXIMO_BITS_CALCULO_ITERATIVO,
)
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import resolver_jacobi_desde_captura

_GRANDE = 2 ** (MAXIMO_BITS_CALCULO_ITERATIVO // 2)
_TERCER_VALOR = Fraction(_GRANDE ** 2 - _GRANDE + 1)


def _captura(maximo: int) -> dict[str, object]:
    return {
        "matriz_a": [[1, _GRANDE], [_GRANDE, 1]], "vector_b": [1, 1],
        "tolerancia": "1/100", "maximo_iteraciones": maximo,
    }


@pytest.mark.parametrize("maximo,codigo", [(3, "MAXIMO_ITERACIONES"), (4, "LIMITE_ARITMETICO")])
def test_jacobi_verifica_tres_barridos_y_rechaza_el_cuarto(maximo: int, codigo: str) -> None:
    """El tercer vector cabe en 4096 bits y el siguiente excede esa cota."""
    resultado = resolver_jacobi_desde_captura(_captura(maximo))

    assert resultado.codigo == codigo
    assert resultado.iteraciones_realizadas == 3
    assert resultado.aproximacion == (_TERCER_VALOR, _TERCER_VALOR)
    assert resultado.residuo == (-_GRANDE ** 3, -_GRANDE ** 3)
    assert _TERCER_VALOR.numerator.bit_length() == MAXIMO_BITS_CALCULO_ITERATIVO
    assert resultado.norma_residuo is not None
    assert resultado.norma_residuo.numerator.bit_length() > MAXIMO_BITS_CALCULO_ITERATIVO
    assert resultado.pasos[-1].vector_nuevo == resultado.aproximacion


def test_gauss_seidel_no_publica_un_barrido_con_una_componente_fuera_de_cota() -> None:
    """La segunda fila del segundo barrido excede la cota y se conserva el primero."""
    resultado = resolver_gauss_seidel_desde_captura(_captura(2))

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.iteraciones_realizadas == 1
    assert resultado.aproximacion == (Fraction(1), Fraction(1 - _GRANDE))
    assert resultado.residuo == (_GRANDE ** 2 - _GRANDE, 0)
    assert resultado.pasos[0].vector_nuevo == resultado.aproximacion
