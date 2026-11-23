"""Paridad y causas de parada de Jacobi desde las capturas de Scalaris."""
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.jacobi import jacobi as motor
from src.backend.resolutores.sistemas_lineales.jacobi.aritmetica_jacobi import LimiteAritmeticoJacobi
from src.frontend.controladores.algebra.sistemas_lineales.nucleo.captura_iterativa import (
    SistemaCapturado, ajustar_variables, interpretar_ecuaciones, redactar_ecuaciones,
)
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.controlador_iterativos import (
    ejemplo_iterativo, resolver_iterativo,
)
from src.frontend.vistas.algebra.sistemas_lineales.resultados.resultado_iterativo import _presentar_escalar


def _captura(sistema: SistemaCapturado, **cambios) -> dict:
    return {
        'modo': 'matriz', 'matriz_a': sistema.matriz, 'vector_b': sistema.independientes,
        'variables': sistema.variables, 'vector_inicial': ['0'] * len(sistema.variables),
        'tolerancia': '0.001', 'maximo_iteraciones': '25', 'matriz_vacia': False, **cambios,
    }


def test_el_ejemplo_conserva_seis_barridos_exactos_en_ambas_capturas():
    """Ambos modos entregan el mismo resultado, incluida la primera sustitución."""
    sistema = ejemplo_iterativo()
    matriz = resolver_iterativo(_captura(sistema))
    ecuaciones = resolver_iterativo(_captura(sistema, modo='ecuaciones', ecuaciones=redactar_ecuaciones(sistema)))
    assert matriz == ecuaciones
    assert matriz['codigo'] == 'TOLERANCIA_ALCANZADA'
    assert len(matriz['pasos']) == 6
    assert matriz['pasos'][0]['vector_nuevo'] == ('5/8', '23/10', '-7/6')


def test_conversion_conserva_ceros_y_nombres_y_rechaza_texto_invalido():
    """La ida y vuelta retiene una columna nula y admite nombres no predeterminados."""
    variables = ajustar_variables(['a_1', 'β'], 3)
    sistema = SistemaCapturado([['1', '0', '0'], ['0', '0', '1/2'], ['0', '0', '0']], ['1', '2', '0'], variables)
    assert interpretar_ecuaciones(redactar_ecuaciones(sistema)) == sistema
    with pytest.raises(ValueError, match='coeficiente'):
        redactar_ecuaciones(SistemaCapturado([['x']], ['0'], ['a']))


@pytest.mark.parametrize(('ecuacion', 'inicio', 'codigo', 'campo'), [
    ('x = 1', '1', 'SOLUCION_EXACTA', None),
    ('x = 1', '9999/10000', 'TOLERANCIA_ALCANZADA', None),
    ('0x = 1', '0', 'DIAGONAL_NULA', 'matriz_a'),
    ('x = 1', '', 'ENTRADA_INVALIDA', 'vector_inicial'),
])
def test_inicio_y_diagnosticos_con_cero_barridos(ecuacion, inicio, codigo, campo):
    """El inicio verificado o una captura inválida producen cero pasos reproducibles."""
    resultado = resolver_iterativo(_captura(interpretar_ecuaciones(ecuacion), vector_inicial=[inicio]))
    assert resultado['codigo'] == codigo
    assert resultado['pasos'] == ()
    if campo:
        assert resultado['diagnostico']['campo'] == campo
        assert resultado['diagnostico']['fila'] == 1


def test_maximo_y_sistema_rectangular_conservan_su_diagnostico():
    """El máximo conserva su último vector y una forma incompatible se atribuye al texto."""
    sistema = ejemplo_iterativo()
    maximo = resolver_iterativo(_captura(sistema, maximo_iteraciones='1'))
    assert maximo['codigo'] == 'MAXIMO_ITERACIONES'
    assert maximo['aproximacion'] == maximo['pasos'][-1]['vector_nuevo']
    rectangular = resolver_iterativo(_captura(sistema, modo='ecuaciones', ecuaciones='x + y = 1'))
    assert rectangular['codigo'] == 'ENTRADA_INVALIDA'
    assert rectangular['diagnostico']['campo'] == 'ecuaciones'
    assert '1 ecuaciones y 2 incógnitas' in rectangular['diagnostico']['mensaje']


@pytest.mark.parametrize('residuos_verificados', [0, 2])
def test_limite_aritmetico_solo_publica_barridos_completos(monkeypatch, residuos_verificados):
    """Preserva el último barrido y omite el vector cuando ni el inicio fue verificable."""
    calcular_residuo = motor.residuo_sistema
    verificados = 0

    def residuo_acotado(*argumentos):
        nonlocal verificados
        if verificados == residuos_verificados:
            raise LimiteAritmeticoJacobi('Se alcanzó el límite aritmético.')
        verificados += 1
        return calcular_residuo(*argumentos)

    monkeypatch.setattr(motor, 'residuo_sistema', residuo_acotado)
    resultado = resolver_iterativo(_captura(ejemplo_iterativo()))
    assert resultado['codigo'] == 'LIMITE_ARITMETICO'
    if residuos_verificados == 0:
        assert resultado['aproximacion'] is None
        assert resultado['residuo'] is None
        assert not resultado['pasos']
    else:
        assert len(resultado['pasos']) == 1
        assert resultado['aproximacion'] == ('5/8', '23/10', '-7/6')


def test_residuo_extenso_se_serializa_y_se_muestra_sin_truncar():
    """Una entrada válida puede producir un residuo con más de 4300 dígitos."""
    coeficientes = [Fraction(1, base**potencia) for base, potencia in ((2, 2000), (3, 1250), (5, 850), (7, 700))]
    inicio = [Fraction(1, base**potencia) for base, potencia in ((11, 570), (13, 540), (17, 490), (19, 465))]
    matriz = [coeficientes, ['0', '1', '0', '0'], ['0', '0', '1', '0'], ['0', '0', '0', '1']]
    sistema = SistemaCapturado(matriz, ['0', *inicio[1:]], ['x1', 'x2', 'x3', 'x4'])
    resultado = resolver_iterativo(_captura(sistema, vector_inicial=inicio))
    assert resultado['codigo'] == 'TOLERANCIA_ALCANZADA'
    norma = resultado['norma_residuo']
    assert len(norma.partition('/')[2]) > 4300
    assert _presentar_escalar('‖r‖∞', norma).endswith(f'(exacto: {norma})')
