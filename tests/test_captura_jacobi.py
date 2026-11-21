"""Entrada cruda y diagnósticos de captura del resolutor de Jacobi."""
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.jacobi.contrato_jacobi import EntradaJacobi
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import (
    resolver_jacobi, resolver_jacobi_desde_captura,
)


def _captura(**campos: object) -> dict[str, object]:
    datos = {
        "matriz_a": [[4, 1], [1, 3]],
        "vector_b": [2, 2],
        "tolerancia": "0.01",
        "maximo_iteraciones": 1,
    }
    return {**datos, **campos}


def _resolver_tipado(captura):
    return resolver_jacobi(EntradaJacobi(**captura))


def test_captura_omitida_empieza_en_cero() -> None:
    """El inicio omitido genera un cero por variable para la iteración simultánea."""
    resultado = resolver_jacobi_desde_captura(_captura())

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert resultado.pasos[0].vector_anterior == (Fraction(0), Fraction(0))
    assert resultado.aproximacion == (Fraction(1, 2), Fraction(2, 3))


@pytest.mark.parametrize("inicio", [None, [], [0], [0, 0, 0]])
def test_captura_con_inicio_invalido_devuelve_el_campo(inicio: object) -> None:
    """Un valor explícito para el inicio se valida con la dimensión de A."""
    resultado = resolver_jacobi_desde_captura(_captura(vector_inicial=inicio))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "vector_inicial"


@pytest.mark.parametrize("coeficiente", [1.0000000001, True, "", "1/0", " " * 256 + "1"])
@pytest.mark.parametrize("resolver", [resolver_jacobi_desde_captura, _resolver_tipado])
def test_captura_rechaza_coeficientes_crudos_invalidos(resolver, coeficiente: object) -> None:
    """La celda inválida se ubica antes de que Matriz pueda normalizarla."""
    resultado = resolver(_captura(matriz_a=[[coeficiente]], vector_b=[1], vector_inicial=[0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "matriz_a"
    assert (resultado.diagnostico.fila, resultado.diagnostico.columna) == (1, 1)


@pytest.mark.parametrize("resolver", [resolver_jacobi_desde_captura, _resolver_tipado])
def test_captura_conserva_el_decimal_exacto_de_la_matriz(resolver) -> None:
    """El decimal textual conserva los dígitos que distinguen su solución de uno."""
    resultado = resolver(_captura(
        matriz_a=[["1.0000000001"]], vector_b=[1], vector_inicial=[1],
        tolerancia="0.000000000001",
    ))

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.iteraciones_realizadas == 1
    assert resultado.aproximacion == (Fraction(10_000_000_000, 10_000_000_001),)
    assert resultado.residuo == (Fraction(0),)


def test_captura_con_fila_larga_informa_la_dimension_esperada() -> None:
    """El mensaje describe el requisito de la fila truncada al copiar."""
    resultado = resolver_jacobi_desde_captura(_captura(matriz_a=[[1] * 100_000], vector_b=[1]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.fila == 1
    assert resultado.diagnostico.mensaje == "La fila 1 de A debe tener exactamente 1 columna."


@pytest.mark.parametrize("resolver", [resolver_jacobi_desde_captura, _resolver_tipado])
def test_rechaza_una_matriz_que_ya_redondeo_un_coeficiente(resolver) -> None:
    """La normalización previa de un flotante no puede producir una certificación."""
    matriz = Matriz(1, 1, [[1.0000000001]])
    assert matriz.obtener(0, 0) == 1
    resultado = resolver(_captura(
        matriz_a=matriz, vector_b=[1], vector_inicial=[1], tolerancia=Fraction(1, 10 ** 12),
    ))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "matriz_a"
    assert resultado.aproximacion is None
