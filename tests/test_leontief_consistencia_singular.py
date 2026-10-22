"""Consistencia exacta, parámetros y presentación de balances sin multiplicador."""
from fractions import Fraction
import json

import pytest
from nicegui import Client, core, ui

from src.frontend.controladores.operaciones_matrices.controlador_leontief import ControladorLeontief
from src.frontend.vistas.operaciones_matrices._renderizado_leontief import renderizar_resultado_leontief


def _resolver(coeficientes, demanda):
    return json.loads(ControladorLeontief.procesar(json.dumps({
        'matriz_coeficientes': coeficientes, 'vector_demanda': demanda,
    })))


@pytest.mark.parametrize('demanda,estado,rango_aumentada', [
    (['3', '6'], 'SOLUCIONES_INFINITAS', 1),
    (['3', '5'], 'SIN_SOLUCION', 2),
])
def test_balance_singular_no_nulo_clasifica_por_consistencia(demanda, estado, rango_aumentada):
    """Una demanda compatible conserva una familia; la incompatible no inventa producción."""
    resultado = _resolver([['0', '-1'], ['-2', '-1']], demanda)
    assert resultado['estado'] == estado
    assert resultado['analisis_sistema']['rango_a'] == 1
    assert resultado['analisis_sistema']['rango_aumentada'] == rango_aumentada
    assert 'vector_produccion' not in resultado and 'matriz_multiplicador_latex' not in resultado
    parametros = resultado['parametros_solucion']
    if estado == 'SIN_SOLUCION':
        assert parametros is None
    else:
        particular = list(map(Fraction, parametros['particular']))
        direccion = list(map(Fraction, parametros['direcciones'][0]))
        for parametro in (-2, 0, 3):
            produccion = [valor + parametro * peso for valor, peso in zip(particular, direccion)]
            assert produccion[0] + produccion[1] == 3
            assert 2 * produccion[0] + 2 * produccion[1] == 6


@pytest.mark.parametrize('demanda,estado', [
    (['1/1000000000000', '0'], 'SIN_SOLUCION'),
    (['0', '0'], 'SOLUCIONES_INFINITAS'),
])
def test_balance_nulo_no_descarta_demanda_exacta_pequena(demanda, estado):
    """La clasificación exacta no confunde una fracción pequeña con demanda cero."""
    resultado = _resolver([['1', '0'], ['0', '1']], demanda)
    assert resultado['estado'] == estado
    assert resultado['analisis_sistema']['rango_a'] == 0


@pytest.mark.parametrize('demanda', [['3', '6'], ['3', '5']])
def test_vista_presenta_balance_singular_sin_tarjeta_de_exito(monkeypatch, demanda):
    """Los estados no únicos no presentan multiplicador ni una producción única."""
    monkeypatch.setattr(core, 'script_mode', False)
    monkeypatch.setattr(ui, 'run_javascript', lambda *argumentos, **opciones: None)
    resultado = _resolver([['0', '-1'], ['-2', '-1']], demanda)
    cliente = Client(ui.page('/leontief_consistencia'))
    try:
        with cliente:
            renderizar_resultado_leontief(resultado)
        etiquetas = [elemento.text for elemento in cliente.elements.values() if isinstance(elemento, ui.label)]
        assert resultado['mensaje'] in etiquetas
        assert not any('Multiplicador de Leontief' in etiqueta for etiqueta in etiquetas)
        assert not any('Vector de producción' in etiqueta for etiqueta in etiquetas)
    finally:
        cliente.delete()
