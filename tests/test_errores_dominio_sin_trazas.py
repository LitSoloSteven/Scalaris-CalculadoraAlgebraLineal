"""Mensajes controlados de sistemas, romanos y conversiones ante entradas límite."""
import json

import pytest

from src.backend.resolutores.sistemas_numericos.calculadora_romana import CalculadoraRomana, ErrorNumeroRomano
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.frontend.controladores.sistemas_lineales.controlador_gauss import ControladorGauss
from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import ControladorGaussJordan


@pytest.mark.parametrize('controlador', [ControladorGauss, ControladorGaussJordan])
def test_sistema_inconsistente_no_publica_trazas(controlador):
    """El sistema de diez ecuaciones conserva su fallo matemático sin traza privada."""
    matriz = [['1' if i == j else '0' for j in range(10)] for i in range(10)]
    matriz[9] = ['0'] * 10
    carga = json.dumps({'matriz_a': matriz, 'vector_b': ['1'] * 9 + ['5']})
    resultado = json.loads(controlador.procesar_sistema(carga))
    assert 'Traceback' not in resultado.get('mensaje', '')
    assert resultado['estado'] == 'SIN_SOLUCION'


def test_error_romano_superior_indica_rango_maximo():
    """La suma que excede 3999 explica su límite sin convertirlo en otro error."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        CalculadoraRomana.sumar('MMMCMXCIX', 'I')
    mensaje = str(captura.value)
    assert '3999' in mensaje or 'rango' in mensaje.lower() or 'máximo' in mensaje.lower()


def test_error_romano_cero_no_publica_trazas():
    """La resta nula conserva el error romano previsto y omite trazas privadas."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        CalculadoraRomana.restar('V', 'V')
    assert 'Traceback' not in str(captura.value)


def test_conversion_grande_no_publica_trazas():
    """La conversión del entero de doscientos bits mantiene una respuesta limpia."""
    resultado = ConversorBases().decimal_a_todo(str(2 ** 200 - 1))
    assert 'Traceback' not in str(resultado)
