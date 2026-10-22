"""Contratos puros de recomendación e historial de las herramientas matriciales."""
import pytest

from src.frontend.controladores.operaciones_matrices.recomendacion_determinante import metodo_recomendado_disponible
from src.frontend.controladores.sesion_matricial import describir_registro


@pytest.mark.parametrize('respuesta,actual,esperado', [
    (None, 'lu', None),
    ({}, 'lu', None),
    ({'estado': 'ERROR', 'metodo_recomendado': 'laplace'}, 'lu', None),
    ({'estado': 'EXITO', 'metodo_recomendado': 'lu'}, 'lu', None),
    ({'estado': 'EXITO', 'metodo_recomendado': 'laplace'}, 'lu', 'laplace'),
    ({'estado': 'EXITO', 'metodo_recomendado': 'lu'}, 'laplace', 'lu'),
])
def test_accion_recomendacion_solo_valida_y_distinta(respuesta, actual, esperado):
    """Solo se ofrece aplicar un método válido distinto de la elección actual."""
    assert metodo_recomendado_disponible(respuesta, actual) == esperado


@pytest.mark.parametrize('estado,valor,metodo,etiqueta,nombre', [
    ('DETERMINANTE_CALCULADO', '1001/1000', 'lu', 'Calculado', 'Eliminación con pivoteo'),
    ('DETERMINANTE_SINGULAR', '0', 'laplace', 'Singular', 'Cofactores'),
])
def test_detalle_determinante_conserva_valor_y_metodo(estado, valor, metodo, etiqueta, nombre):
    """Un determinante singular también tiene estado y detalle propios."""
    resultado = describir_registro({'dimension': 50, 'estado': estado, 'determinante': valor, 'metodo': metodo})
    assert resultado['dimensiones'] == '50×50'
    assert resultado['estado'] == etiqueta
    assert resultado['detalle'] == f'det = {valor}. Método: {nombre}'


@pytest.mark.parametrize('estado,etiqueta,clase', [
    ('SOLUCION_UNICA', 'Solución Única', 'texto-acento'),
    ('SOLUCIONES_INFINITAS', 'Infinitas Soluciones', 'texto-advertencia'),
    ('SIN_SOLUCION', 'Sin Solución', 'sesion-error'),
])
def test_historial_sistemas_conserva_contrato(estado, etiqueta, clase):
    """Los registros de sistemas mantienen etiquetas, clases y método."""
    assert describir_registro({'filas': 2, 'columnas': 3, 'estado': estado, 'metodo': 'gauss-jordan'}) == {
        'dimensiones': '2×3', 'estado': etiqueta, 'clase': clase, 'detalle': 'Método: Gauss Jordan'}


@pytest.mark.parametrize('estado,etiqueta,clase,valor', [
    ('EXITO', 'Invertible', 'texto-acento', '2'),
    ('SINGULAR', 'Singular', 'sesion-error', '0'),
])
def test_historial_inversa_conserva_contrato(estado, etiqueta, clase, valor):
    """Inversa conserva los estados y el detalle que ya mostraba."""
    assert describir_registro({'dimension': 2, 'estado': estado, 'determinante': valor}) == {
        'dimensiones': '2×2', 'estado': etiqueta, 'clase': clase, 'detalle': f'det = {valor}'}


def test_registro_incompleto_o_futuro_no_interrumpe_historial():
    """Los estados futuros degradan a Error y los registros incompletos se describen."""
    assert describir_registro({'estado': 'DETERMINANTE_ERROR'})['estado'] == 'Error'
    resultado = describir_registro({'estado': 'DETERMINANTE_CALCULADO', 'metodo': 'desconocido'})
    assert resultado['estado'] == 'Calculado'
