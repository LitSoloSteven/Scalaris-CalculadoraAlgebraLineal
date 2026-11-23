"""Aceptación exacta, presupuestos reales e inmutabilidad de Gauss-Seidel."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction

import pytest

import src.backend.resolutores.sistemas_lineales.gauss_seidel.gauss_seidel as motor
from src.backend.resolutores.sistemas_lineales.gauss_seidel import ResultadoGaussSeidel
from src.backend.resolutores.sistemas_lineales.gauss_seidel.limites_gauss_seidel import (
    MAXIMO_BITS_CALCULO_GAUSS_SEIDEL,
)

_VECTORES_VERIFICADOS = (
    (Fraction(0), Fraction(0)),
    (Fraction(1, 2), Fraction(1, 2)),
    (Fraction(3, 8), Fraction(13, 24)),
)
_RESIDUOS_VERIFICADOS = (
    (Fraction(2), Fraction(2)),
    (Fraction(-1, 2), Fraction(0)),
    (Fraction(-1, 24), Fraction(0)),
)


def _captura(tolerancia: str = "1/100", maximo: int = 2) -> dict[str, object]:
    return {
        "matriz_a": [[4, 1], [1, 3]],
        "vector_b": [2, 2],
        "vector_inicial": [0, 0],
        "tolerancia": tolerancia,
        "maximo_iteraciones": maximo,
    }


def _limitar_operaciones(monkeypatch: pytest.MonkeyPatch, operaciones: int) -> None:
    configuracion = replace(
        motor.CONFIGURACION_ARITMETICA_GAUSS_SEIDEL, maximo_operaciones=operaciones,
    )
    monkeypatch.setattr(motor, "CONFIGURACION_ARITMETICA_GAUSS_SEIDEL", configuracion)


def _comprobar_vector_verificado(resultado: ResultadoGaussSeidel, iteraciones: int) -> None:
    assert resultado.iteraciones_realizadas == iteraciones
    assert resultado.aproximacion == _VECTORES_VERIFICADOS[iteraciones]
    assert resultado.residuo == _RESIDUOS_VERIFICADOS[iteraciones]
    assert resultado.norma_residuo == max(abs(valor) for valor in resultado.residuo)


def test_las_normas_de_cada_barrido_coinciden_con_las_fracciones_manuales() -> None:
    """Los cambios son 1/2 y 1/8; los residuos son 1/2 y 1/24."""
    resultado = motor.resolver_gauss_seidel_desde_captura(_captura())

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    _comprobar_vector_verificado(resultado, 2)
    assert [(paso.indice, paso.norma_cambio, paso.norma_residuo)
            for paso in resultado.pasos] == [
        (1, Fraction(1, 2), Fraction(1, 2)),
        (2, Fraction(1, 8), Fraction(1, 24)),
    ]


def test_un_inicio_no_nulo_conserva_los_valores_anteriores_y_nuevos() -> None:
    """La primera fila usa el y anterior y la segunda usa el x recién calculado."""
    captura = _captura(maximo=1)
    captura["vector_inicial"] = [1, -1]
    resultado = motor.resolver_gauss_seidel_desde_captura(captura)
    paso = resultado.pasos[0]

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert paso.vector_anterior == (Fraction(1), Fraction(-1))
    assert paso.vector_nuevo == (Fraction(3, 4), Fraction(5, 12))
    assert paso.norma_cambio == paso.norma_residuo == Fraction(17, 12)
    assert resultado.residuo == (Fraction(-17, 12), Fraction(0))


def test_las_fracciones_y_decimales_de_captura_se_calculan_exactamente() -> None:
    """Una captura mixta produce (2, -1/12) y residuo (1/48, 0) sin redondeos."""
    captura = _captura(tolerancia="1/1000", maximo=1)
    captura.update(matriz_a=[["1/2", "0.25"], ["1/3", "2"]], vector_b=["1", "1/2"])
    resultado = motor.resolver_gauss_seidel_desde_captura(captura)

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert resultado.aproximacion == (Fraction(2), Fraction(-1, 12))
    assert resultado.residuo == (Fraction(1, 48), Fraction(0))
    assert resultado.norma_residuo == Fraction(1, 48)
    assert resultado.pasos[0].norma_cambio == Fraction(2)


@pytest.mark.parametrize("operaciones,iteraciones", [(14, 0), (27, 0), (32, 1), (45, 1)])
def test_un_presupuesto_real_descarta_el_barrido_sin_verificar(
    monkeypatch: pytest.MonkeyPatch, operaciones: int, iteraciones: int,
) -> None:
    """Agotar cargos dentro de una fila o del residuo conserva el último barrido completo."""
    _limitar_operaciones(monkeypatch, operaciones)
    captura = _captura()
    original = deepcopy(captura)
    resultado = motor.resolver_gauss_seidel_desde_captura(captura)

    assert resultado.codigo == "LIMITE_ARITMETICO"
    _comprobar_vector_verificado(resultado, iteraciones)
    assert captura == original
    assert resultado.diagnostico is not None
    assert "presupuesto de operaciones" in resultado.diagnostico.mensaje


@pytest.mark.parametrize("operaciones,tolerancia,codigo,iteraciones", [
    (27, "1/2", "LIMITE_ARITMETICO", 0),
    (28, "1/2", "TOLERANCIA_ALCANZADA", 1),
    (46, "1/24", "TOLERANCIA_ALCANZADA", 2),
])
def test_el_ultimo_cargo_certifica_la_tolerancia_antes_del_maximo(
    monkeypatch: pytest.MonkeyPatch, operaciones: int, tolerancia: str,
    codigo: str, iteraciones: int,
) -> None:
    """Sin el cargo del residuo no hay paso; con él se certifica incluso el último barrido."""
    _limitar_operaciones(monkeypatch, operaciones)
    resultado = motor.resolver_gauss_seidel_desde_captura(_captura(tolerancia))

    assert resultado.codigo == codigo
    _comprobar_vector_verificado(resultado, iteraciones)


def test_un_desborde_real_en_la_segunda_componente_no_publica_la_primera() -> None:
    """La fila inicial calcula 2; la siguiente excede el límite de bits y revierte el barrido."""
    captura = _captura(maximo=1)
    coeficiente = 2 ** (MAXIMO_BITS_CALCULO_GAUSS_SEIDEL - 1)
    captura.update(matriz_a=[[1, 0], [coeficiente, 1]], vector_b=[2, 0])
    original = deepcopy(captura)
    resultado = motor.resolver_gauss_seidel_desde_captura(captura)

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.aproximacion == (Fraction(0), Fraction(0))
    assert resultado.residuo == (Fraction(2), Fraction(0))
    assert resultado.norma_residuo == Fraction(2)
    assert resultado.iteraciones_realizadas == 0
    assert resultado.pasos == ()
    assert resultado.diagnostico is not None
    assert "tamaño máximo" in resultado.diagnostico.mensaje
    assert captura == original


def test_el_resultado_y_los_pasos_historicos_impiden_mutaciones() -> None:
    """El segundo barrido y los intentos de edición no alteran el primer vector guardado."""
    resultado = motor.resolver_gauss_seidel_desde_captura(_captura())
    primero, segundo = resultado.pasos

    with pytest.raises(FrozenInstanceError):
        setattr(resultado, "pasos", ())
    with pytest.raises(FrozenInstanceError):
        setattr(primero, "vector_nuevo", segundo.vector_nuevo)
    with pytest.raises(TypeError):
        primero.vector_nuevo[0] = Fraction(99)
    assert primero.vector_nuevo == _VECTORES_VERIFICADOS[1]
    assert segundo.vector_anterior == _VECTORES_VERIFICADOS[1]
    assert segundo.vector_nuevo == _VECTORES_VERIFICADOS[2]
