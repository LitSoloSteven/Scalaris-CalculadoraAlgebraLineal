"""Paridad exacta y prioridad de errores de los adaptadores de sistemas e inversa."""
from fractions import Fraction
import json
from unittest.mock import Mock

import pytest

from src.backend.resolutores.operaciones_matrices.captura_inversa import validar_y_parsear_matriz_cuadrada
from src.backend.resolutores.sistemas_lineales.captura import validar_y_construir_aumentada


@pytest.mark.parametrize("valor,esperado", [(None, Fraction(0)), (" ", Fraction(0)),
                                          ("1001/1000", Fraction(1001, 1000)), ("0.125", Fraction(1, 8))])
def test_ambos_adaptadores_conservan_ceros_y_fracciones(valor, esperado):
    """Vacío/None y números exactos conservan tipo y valor en ambos consumidores."""
    inversa, dimension, error = validar_y_parsear_matriz_cuadrada({"dimension": 1, "datos": [[valor]]})
    sistema, coeficientes, terminos, filas, columnas, error_sistema = validar_y_construir_aumentada({"matriz_a": [[valor]], "vector_b": [valor]})
    assert error is None and error_sistema is None
    assert dimension == filas == columnas == 1
    assert inversa.datos == coeficientes == [[esperado]]
    assert terminos == [esperado]
    assert sistema.datos == [[esperado, esperado]]


@pytest.mark.parametrize("en_matriz", [True, False])
def test_sistema_conserva_coordenada_y_prioridad_del_primer_error(en_matriz):
    """El error matricial precede al vector y el JSON conserva su texto histórico."""
    datos = {"matriz_a": [["abc" if en_matriz else "1"]], "vector_b": ["abc"]}
    resultado = validar_y_construir_aumentada(datos)
    mensaje = json.loads(resultado[-1])["mensaje"]
    assert resultado[:5] == (None, None, None, 0, 0)
    assert mensaje.startswith("Error en A[1,1]:" if en_matriz else "Error en b[1]:")


def test_inversa_conserva_coordenada_y_mensaje_del_primer_error():
    """La captura compartida mantiene la ubicación cero basada del fallo de inversa."""
    matriz, dimension, error = validar_y_parsear_matriz_cuadrada({"dimension": 2, "datos": [[1, "abc"], ["abc", 1]]})
    assert matriz is None and dimension == 2
    assert error["celda_error"] == [0, 1]
    assert error["mensaje"].startswith("Error en A[1,2]:")


def test_los_dos_adaptadores_invocan_el_parser_compartido(monkeypatch):
    """La instrumentación comprueba delegación de celdas y política de vacíos."""
    parser = Mock(return_value=Fraction(3, 2))
    monkeypatch.setattr("src.backend.resolutores.sistemas_lineales.captura.parsear_celda_exacta", parser)
    monkeypatch.setattr("src.backend.resolutores.operaciones_matrices.captura_inversa.parsear_celda_exacta", parser)
    validar_y_construir_aumentada({"matriz_a": [[None]], "vector_b": [""]})
    validar_y_parsear_matriz_cuadrada({"dimension": 1, "datos": [[None]]})
    assert parser.call_count == 3
    assert [llamada.args[1] for llamada in parser.call_args_list] == ["Error en A[1,1]", "Error en b[1]", "Error en A[1,1]"]
    assert all(llamada.kwargs == {"vacio_como_cero": True} for llamada in parser.call_args_list)
