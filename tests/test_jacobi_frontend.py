"""Paridad y causas de parada de Jacobi desde las capturas de Scalaris."""
import pytest

from src.frontend.controladores.algebra.sistemas_lineales.nucleo.captura_iterativa import (
    SistemaCapturado, ajustar_variables, interpretar_ecuaciones, redactar_ecuaciones,
)
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.controlador_iterativos import (
    ejemplo_iterativo, resolver_iterativo,
)


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
