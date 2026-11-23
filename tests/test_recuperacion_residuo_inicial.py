"""Recuperación verificable ante un residuo inicial que excede su cota de bits."""
from collections.abc import Callable
from dataclasses import replace
from fractions import Fraction
from types import ModuleType

import pytest

import src.backend.resolutores.sistemas_lineales.gauss_seidel.gauss_seidel as motor_gauss_seidel
import src.backend.resolutores.sistemas_lineales.jacobi.jacobi as motor_jacobi
from src.backend.resolutores.sistemas_lineales.gauss_seidel import ResultadoGaussSeidel
from src.backend.resolutores.sistemas_lineales.gauss_seidel.limites_gauss_seidel import (
    CONFIGURACION_ARITMETICA_GAUSS_SEIDEL,
)
from src.backend.resolutores.sistemas_lineales.iterativos.aritmetica_iterativa import (
    ConfiguracionAritmetica, PresupuestoAritmetico,
)
from src.backend.resolutores.sistemas_lineales.iterativos.contrato_iterativo import ResultadoIterativo
from src.backend.resolutores.sistemas_lineales.jacobi.contrato_jacobi import ResultadoJacobi

ResolutorCaptura = Callable[[object], ResultadoIterativo]
Metodo = tuple[ModuleType, ResolutorCaptura, type[ResultadoIterativo]]
METODOS = (
    (motor_gauss_seidel, motor_gauss_seidel.resolver_gauss_seidel_desde_captura, ResultadoGaussSeidel),
    (motor_jacobi, motor_jacobi.resolver_jacobi_desde_captura, ResultadoJacobi),
)
_COEFICIENTE = Fraction(1, 2 ** 2050)
_SOLUCION = Fraction(2 ** 2050)


def _captura() -> dict[str, object]:
    return {
        "matriz_a": [[_COEFICIENTE]], "vector_b": [1],
        "vector_inicial": [_COEFICIENTE], "tolerancia": "1/100", "maximo_iteraciones": 1,
    }


def _inyectar_presupuesto(
    monkeypatch: pytest.MonkeyPatch, modulo: ModuleType, configuracion: ConfiguracionAritmetica,
) -> PresupuestoAritmetico:
    presupuesto = PresupuestoAritmetico(configuracion)
    monkeypatch.setattr(modulo, "PresupuestoAritmetico", lambda *argumentos: presupuesto)
    return presupuesto


@pytest.mark.parametrize("metodo", METODOS)
def test_un_residuo_inicial_grande_permite_encontrar_una_solucion_verificada(metodo: Metodo) -> None:
    """El sistema escalar con denominador 2^2050 se resuelve en un barrido exacto."""
    modulo, resolver, clase_resultado = metodo
    resultado = resolver(_captura())

    assert type(resultado) is clase_resultado
    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == (_SOLUCION,)
    assert resultado.residuo == (Fraction(0),)
    assert resultado.norma_residuo == 0
    assert resultado.iteraciones_realizadas == 1
    assert resultado.pasos[0].vector_anterior == (_COEFICIENTE,)
    assert resultado.pasos[0].vector_nuevo == (_SOLUCION,)


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("operaciones,codigo,iteraciones", [
    (2, "LIMITE_ARITMETICO", 0),
    (7, "LIMITE_ARITMETICO", 0),
    (8, "SOLUCION_EXACTA", 1),
])
def test_la_recuperacion_conserva_los_cargos_y_solo_publica_estados_verificados(
    metodo: Metodo, monkeypatch: pytest.MonkeyPatch,
    operaciones: int, codigo: str, iteraciones: int,
) -> None:
    """El intento inicial cuesta tres cargos y el primer barrido verificable requiere ocho."""
    modulo, resolver, clase_resultado = metodo
    configuracion = replace(CONFIGURACION_ARITMETICA_GAUSS_SEIDEL, maximo_operaciones=operaciones)
    presupuesto = _inyectar_presupuesto(monkeypatch, modulo, configuracion)
    resultado = resolver(_captura())

    assert type(resultado) is clase_resultado
    assert resultado.codigo == codigo
    assert resultado.iteraciones_realizadas == iteraciones
    assert presupuesto.restantes == operaciones - (3 if operaciones == 2 else 8)
    if iteraciones:
        assert resultado.aproximacion == (_SOLUCION,)
        assert resultado.residuo == (Fraction(0),)
    elif operaciones == 7:
        residuo_inicial = 1 - _COEFICIENTE ** 2
        assert resultado.aproximacion == (_COEFICIENTE,)
        assert resultado.residuo == (residuo_inicial,)
        assert resultado.norma_residuo == residuo_inicial
        assert resultado.pasos == ()
    else:
        assert resultado.aproximacion is None
        assert resultado.residuo is None
        assert resultado.norma_residuo is None
        assert resultado.pasos == ()


@pytest.mark.parametrize("metodo", METODOS)
def test_un_limite_de_acumulacion_inicial_no_habilita_el_barrido(
    metodo: Metodo, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El desborde del producto escalar conserva su bloqueo y sus dos cargos consumidos."""
    modulo, resolver, clase_resultado = metodo
    configuracion = replace(CONFIGURACION_ARITMETICA_GAUSS_SEIDEL, maximo_bits_acumulacion=8)
    presupuesto = _inyectar_presupuesto(monkeypatch, modulo, configuracion)
    captura = _captura()
    captura.update(matriz_a=[[16]], vector_b=[1], vector_inicial=[16])
    resultado = resolver(captura)

    assert type(resultado) is clase_resultado
    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.aproximacion is None
    assert resultado.iteraciones_realizadas == 0
    assert presupuesto.restantes == configuracion.maximo_operaciones - 2


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("maximo", [1, 2])
def test_el_primer_barrido_verificado_puede_continuar_hasta_una_solucion(
    metodo: Metodo, maximo: int,
) -> None:
    """Una recuperación no exacta conserva el primer paso y alcanza (0, 1) en el segundo."""
    modulo, resolver, clase_resultado = metodo
    captura = _captura()
    captura.update(matriz_a=[[_COEFICIENTE, 1], [0, 1]], vector_b=[1, 1],
                   vector_inicial=[_COEFICIENTE, 0], maximo_iteraciones=maximo)
    resultado = resolver(captura)

    assert type(resultado) is clase_resultado
    assert resultado.iteraciones_realizadas == maximo
    assert resultado.pasos[0].vector_nuevo == (_SOLUCION, Fraction(1))
    if maximo == 1:
        assert resultado.codigo == "MAXIMO_ITERACIONES"
        assert resultado.aproximacion == (_SOLUCION, Fraction(1))
        assert resultado.residuo == (Fraction(-1), Fraction(0))
    else:
        assert resultado.codigo == "SOLUCION_EXACTA"
        assert resultado.aproximacion == (Fraction(0), Fraction(1))
        assert resultado.residuo == (Fraction(0), Fraction(0))


@pytest.mark.parametrize("metodo", METODOS)
def test_un_limite_posterior_conserva_el_primer_barrido_recuperado(
    metodo: Metodo, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Con cuarenta cargos no se verifica el segundo barrido y se conserva el primero."""
    modulo, resolver, clase_resultado = metodo
    configuracion = replace(CONFIGURACION_ARITMETICA_GAUSS_SEIDEL, maximo_operaciones=40)
    _inyectar_presupuesto(monkeypatch, modulo, configuracion)
    captura = _captura()
    captura.update(matriz_a=[[_COEFICIENTE, 1], [0, 1]], vector_b=[1, 1],
                   vector_inicial=[_COEFICIENTE, 0], maximo_iteraciones=2)
    resultado = resolver(captura)

    assert type(resultado) is clase_resultado
    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.iteraciones_realizadas == 1
    assert resultado.aproximacion == (_SOLUCION, Fraction(1))
    assert resultado.residuo == (Fraction(-1), Fraction(0))
    assert resultado.pasos[0].vector_nuevo == resultado.aproximacion
