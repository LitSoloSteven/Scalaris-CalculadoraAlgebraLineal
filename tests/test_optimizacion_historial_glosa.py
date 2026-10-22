"""Conservación de mensajes y publicación única del historial observable."""
import json
import pytest
from nicegui.observables import ObservableDict
from src.frontend.componentes.historial_glosa import incorporar_mensaje


@pytest.mark.parametrize('cantidad', [0, 1, 59, 60, 61])
def test_historial_equivale_a_anexar_y_podar_sin_truncar(cantidad):
    """La salida conserva el límite, orden y texto exacto de la política anterior."""
    historial = [{'texto': str(indice) + 'ñ' * 4000, 'enviado': bool(indice % 2)} for indice in range(cantidad)]
    mensaje = {'texto': '漢字' * 2000, 'error': False, 'enviado': False}
    esperado = [*historial, mensaje][-60:]
    resultado = incorporar_mensaje(historial, mensaje)
    assert json.dumps(resultado, ensure_ascii=False) == json.dumps(esperado, ensure_ascii=False)
    assert len(historial) == cantidad
    assert resultado[-1]['texto'] == mensaje['texto']


def test_actualizacion_del_historial_emite_un_evento_en_el_limite():
    """El historial completo se publica una vez en lugar de append y poda separados."""
    almacen = ObservableDict({'historial': [{'texto': str(indice)} for indice in range(60)]})
    cambios = []
    almacen.on_change(lambda: cambios.append(1))
    almacen['historial'] = incorporar_mensaje(almacen['historial'], {'texto': 'nuevo'})
    assert cambios == [1]
    assert len(almacen['historial']) == 60
    assert almacen['historial'][0]['texto'] == '1'
