"""Paridad, operandos exactos y causas de parada de Gauss-Seidel en Scalaris."""
import pytest

from src.backend.resolutores.sistemas_lineales.gauss_seidel import gauss_seidel as motor
from src.backend.resolutores.sistemas_lineales.iterativos.aritmetica_iterativa import LimiteAritmeticoIterativo
from src.frontend.controladores.algebra.sistemas_lineales.nucleo.captura_iterativa import redactar_ecuaciones
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.controlador_iterativos import (
    ejemplo_iterativo, resolver_iterativo,
)
from src.frontend.nucleo.textos.textos_metodos_iterativos import CAUSAS_PARADA, METODO_SECUENCIAL
from src.frontend.vistas.algebra.sistemas_lineales.resultados.pasos_iterativos import _despeje


def _captura(**cambios) -> dict:
    sistema = ejemplo_iterativo()
    return {
        'metodo': METODO_SECUENCIAL, 'modo': 'matriz', 'matriz_a': sistema.matriz,
        'vector_b': sistema.independientes, 'variables': sistema.variables, 'matriz_vacia': False,
        'vector_inicial': ['0', '0', '0'], 'tolerancia': '0.001', 'maximo_iteraciones': '25', **cambios,
    }


def test_ambas_capturas_presentan_los_operandos_secuenciales():
    """El segundo despeje toma x1 del barrido nuevo y x3 del anterior."""
    matriz = resolver_iterativo(_captura())
    ecuaciones = resolver_iterativo(_captura(modo='ecuaciones', ecuaciones=redactar_ecuaciones(ejemplo_iterativo())))
    assert matriz == ecuaciones
    assert matriz['codigo'] == 'TOLERANCIA_ALCANZADA'
    assert len(matriz['pasos']) == 4
    primero = matriz['pasos'][0]
    assert primero['vector_nuevo'][:2] == ('5/8', '87/40')
    despeje = _despeje(primero, matriz['entrada_canonica'], 1, matriz['metodo'])
    assert r'\underbrace{\left(\frac{5}{8}\right)}_{x_{1}^{(1)}}' in despeje
    assert r'\underbrace{\left(0\right)}_{x_{3}^{(0)}}' in despeje
    assert despeje.endswith(r'= \frac{87}{40}')


def test_inicio_no_nulo_se_conserva_en_la_sustitucion():
    """Usa x3 inicial y x1 actualizado al calcular x2."""
    resultado = resolver_iterativo(_captura(vector_inicial=['1', '2', '3']))
    primero = resultado['pasos'][0]
    assert primero['vector_anterior'] == ('1', '2', '3')
    assert primero['vector_nuevo'][:2] == ('1/2', '5/2')
    despeje = _despeje(primero, resultado['entrada_canonica'], 1, resultado['metodo'])
    assert r'\underbrace{\left(3\right)}_{x_{3}^{(0)}}' in despeje


@pytest.mark.parametrize(('cambios', 'codigo', 'barridos', 'campo'), [
    ({}, 'TOLERANCIA_ALCANZADA', 4, None),
    ({'modo': 'ecuaciones', 'ecuaciones': 'x = 1', 'vector_inicial': ['1']}, 'SOLUCION_EXACTA', 0, None),
    ({'modo': 'ecuaciones', 'ecuaciones': '0x = 1', 'vector_inicial': ['0']}, 'DIAGONAL_NULA', 0, 'matriz_a'),
    ({'vector_inicial': ['', '0', '0']}, 'ENTRADA_INVALIDA', 0, 'vector_inicial'),
    ({'maximo_iteraciones': '1'}, 'MAXIMO_ITERACIONES', 1, None),
])
def test_causas_de_parada_comparten_el_contrato_de_presentacion(cambios, codigo, barridos, campo):
    """Las salidas se pueden mostrar con el mismo código, traza y diagnóstico."""
    resultado = resolver_iterativo(_captura(**cambios))
    assert resultado['codigo'] == codigo
    assert CAUSAS_PARADA[codigo]
    assert len(resultado['pasos']) == barridos
    if campo:
        assert resultado['diagnostico']['campo'] == campo


def test_limite_aritmetico_preserva_el_ultimo_barrido_completo(monkeypatch):
    """Un límite tras el primer barrido retiene su aproximación exacta."""
    siguiente = motor._siguiente_vector

    def siguiente_acotado(preparada, anterior, presupuesto):
        """Agota el presupuesto al intentar el segundo barrido."""
        if any(anterior):
            raise LimiteAritmeticoIterativo('Se alcanzó el límite aritmético.')
        return siguiente(preparada, anterior, presupuesto)

    monkeypatch.setattr(motor, '_siguiente_vector', siguiente_acotado)
    resultado = resolver_iterativo(_captura())
    assert resultado['codigo'] == 'LIMITE_ARITMETICO'
    assert CAUSAS_PARADA[resultado['codigo']]
    assert len(resultado['pasos']) == 1
    assert resultado['aproximacion'] == resultado['pasos'][0]['vector_nuevo']
