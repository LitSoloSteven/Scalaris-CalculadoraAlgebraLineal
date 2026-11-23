"""Igualdad histórica, serialización canónica y explicación sin prometer unicidad."""
from collections.abc import Callable
from dataclasses import asdict, replace
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.gauss_seidel import (
    resolver_gauss_seidel_desde_captura,
)
from src.backend.resolutores.sistemas_lineales.iterativos.contrato_iterativo import (
    ResultadoIterativo,
)
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import (
    resolver_jacobi_desde_captura,
)

ResolutorCaptura = Callable[[object], ResultadoIterativo]
RESOLUTORES = (resolver_gauss_seidel_desde_captura, resolver_jacobi_desde_captura)


def _resultado(resolver: ResolutorCaptura) -> ResultadoIterativo:
    return resolver({
        "matriz_a": [[1]], "vector_b": [1], "vector_inicial": [0],
        "tolerancia": "1/100", "maximo_iteraciones": 1,
    })


@pytest.mark.parametrize("resolver", RESOLUTORES)
def test_los_metadatos_no_cambian_la_igualdad_ni_el_hash(resolver: ResolutorCaptura) -> None:
    """Cambiar u omitir la entrada canónica conserva la igualdad de los campos históricos."""
    resultado = _resultado(resolver)
    assert resultado.entrada_canonica is not None
    otra_entrada = replace(resultado.entrada_canonica, maximo_iteraciones=2)
    otro = replace(resultado, entrada_canonica=otra_entrada)
    historico = replace(resultado, entrada_canonica=None)

    assert resultado == otro == historico
    assert hash(resultado) == hash(otro) == hash(historico)
    assert asdict(resultado) != asdict(otro)


@pytest.mark.parametrize("resolver", RESOLUTORES)
def test_asdict_incluye_la_entrada_canonica_como_metadato(resolver: ResolutorCaptura) -> None:
    """La serialización aditiva conserva los racionales y todos los parámetros validados."""
    resultado = _resultado(resolver)
    serializado = asdict(resultado)

    assert set(serializado) == {
        "codigo", "aproximacion", "residuo", "norma_residuo", "dominancia_estricta",
        "pasos", "diagnostico", "entrada_canonica",
    }
    assert serializado["entrada_canonica"] == {
        "matriz": ((Fraction(1),),),
        "vector_b": (Fraction(1),),
        "vector_inicial": (Fraction(0),),
        "tolerancia": Fraction(1, 100),
        "maximo_iteraciones": 1,
        "dominancia_estricta": True,
    }
    assert asdict(replace(resultado, entrada_canonica=None))["entrada_canonica"] is None


@pytest.mark.parametrize("resolver", RESOLUTORES)
@pytest.mark.parametrize("inicio", [(2, 0), (0, 2)])
def test_un_sistema_con_varias_soluciones_no_promete_unicidad(
    resolver: ResolutorCaptura, inicio: tuple[int, int],
) -> None:
    """Dos vectores distintos satisfacen el mismo sistema singular y se describen como soluciones."""
    resultado = resolver({
        "matriz_a": [[1, 1], [1, 1]], "vector_b": [2, 2], "vector_inicial": inicio,
        "tolerancia": "1/100", "maximo_iteraciones": 1,
    })

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == inicio
    assert "una solución exacta" in resultado.explicacion
    assert "la solución exacta" not in resultado.explicacion


def test_la_solucion_encontrada_en_un_barrido_tampoco_promete_unicidad() -> None:
    """Gauss-Seidel encuentra (2, 0) sin afirmar que sea la única solución del sistema."""
    resultado = resolver_gauss_seidel_desde_captura({
        "matriz_a": [[1, 1], [1, 1]], "vector_b": [2, 2],
        "tolerancia": "1/100", "maximo_iteraciones": 1,
    })

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == (Fraction(2), Fraction(0))
    assert resultado.iteraciones_realizadas == 1
    assert "encontró una solución exacta" in resultado.explicacion
