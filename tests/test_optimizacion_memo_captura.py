"""Vigencia, aislamiento y mutabilidad de los datos reutilizados de Glosa."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from src.ai.huellas import calcular_huella
from src.frontend.controladores.memo_captura import reutilizar_captura
from src.frontend.controladores.operaciones_inversas.contexto import obtener_contexto_inversa, obtener_senales_inversa


def _vista(datos):
    panel = SimpleNamespace(dimension=len(datos), esta_vacio=lambda: False, obtener_datos_matriz=lambda: datos)
    return SimpleNamespace(panel_matriz_cuadrada=panel, _revision_captura=1,
                           _huella_resultado=calcular_huella({'datos': datos}),
                           ultimo_resultado={'estado': 'EXITO', 'determinante_texto': '1'})


def test_memo_invalida_revision_clave_y_valor_fallido():
    """Una revisión nueva descarta todos los derivados; los errores no se retienen."""
    vista = SimpleNamespace(_revision_captura=1)
    construir = Mock(side_effect=[1, 2, 3, ValueError('inválido'), 4])
    assert reutilizar_captura(vista, 'dato', (), construir) == 1
    assert reutilizar_captura(vista, 'dato', (), construir) == 1
    vista._revision_captura += 1
    assert reutilizar_captura(vista, 'dato', (), construir) == 2
    assert reutilizar_captura(vista, 'dato', (2,), construir) == 3
    with pytest.raises(ValueError, match='inválido'):
        reutilizar_captura(vista, 'otro', (2,), construir)
    assert reutilizar_captura(vista, 'otro', (2,), construir) == 4


def test_sin_revision_no_se_memoiza_y_los_clientes_son_independientes():
    """Los consumidores sin notificaciones y dos vistas nunca comparten un derivado."""
    construir = Mock(side_effect=[1, 2, 3, 4])
    externa = SimpleNamespace()
    assert reutilizar_captura(externa, 'dato', (), construir) == 1
    assert reutilizar_captura(externa, 'dato', (), construir) == 2
    assert reutilizar_captura(SimpleNamespace(_revision_captura=1), 'dato', (), construir) == 3
    assert reutilizar_captura(SimpleNamespace(_revision_captura=1), 'dato', (), construir) == 4


def test_contexto_foco_y_entrada_no_contaminan_consultas_posteriores():
    """El contexto se entrega independiente aunque su descriptor provenga de la misma captura."""
    vista = _vista([['1/7']])
    primero = obtener_contexto_inversa(vista)
    primero.entrada['A']['datos'][0][0] = 'contaminado'
    primero.resultado['determinante'] = 'alterado'
    primero.foco = object()
    segundo = obtener_contexto_inversa(vista)
    assert segundo.entrada['A']['datos'] == [['1/7']]
    assert segundo.resultado['determinante'] == '1'
    assert segundo.foco is None


def test_huella_y_resultado_se_consultan_aun_sin_editar_la_captura():
    """Actualizar el resultado o su huella no conserva un resumen obsoleto."""
    vista = _vista([['1']])
    assert not obtener_contexto_inversa(vista).desactualizado
    vista._huella_resultado = 'otra'
    assert obtener_contexto_inversa(vista).resultado is None
    vista._huella_resultado = None
    vista.ultimo_resultado = {'estado': 'SINGULAR'}
    assert obtener_contexto_inversa(vista).resultado['estado'] == 'SINGULAR'


def test_error_fuera_de_la_ventana_y_edicion_restaurada_invalidan_memo():
    """La ventana no oculta errores remotos; una nueva revisión vuelve a validar."""
    datos = [['1'] * 50 for _ in range(50)]
    vista = _vista(datos)
    assert obtener_senales_inversa(vista).invalida is None
    datos[49][49] = 'inválido'
    vista._revision_captura += 1
    assert obtener_contexto_inversa(vista).entrada['A']['invalidos'] == 1
    assert obtener_senales_inversa(vista).invalida.foco == (49, 49)
    assert obtener_contexto_inversa(vista).desactualizado
    datos[49][49] = '1'
    vista._revision_captura += 1
    assert obtener_senales_inversa(vista).invalida is None
    assert not obtener_contexto_inversa(vista).desactualizado


def test_cambio_de_panel_y_dimension_no_reutiliza_captura_anterior():
    """La clave incluye origen y dimensiones aunque la revisión coincida."""
    vista = _vista([['1']])
    obtener_contexto_inversa(vista)
    otra = _vista([['2', '3'], ['4', '5']])
    vista.panel_matriz_cuadrada = otra.panel_matriz_cuadrada
    assert obtener_contexto_inversa(vista).entrada['A']['datos'] == [['2', '3'], ['4', '5']]
