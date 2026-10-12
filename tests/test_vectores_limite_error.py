"""Límite de presentación de errores para celdas vectoriales excesivas."""
import json

from src.frontend.controladores.operaciones_vectores import ControladorOperacionesVectores


def test_error_vectorial_no_refleja_celda_excesiva():
    """El parser rechaza una celda grande sin duplicar todo su contenido en la respuesta."""
    carga = {"scalar": "2", "v": {"orientation": "column", "data": ["9" * 100000]}}
    respuesta = ControladorOperacionesVectores.procesar_multiplicacion_escalar(json.dumps(carga))
    assert json.loads(respuesta)["status"] == "ERROR"
    assert len(respuesta) < 300


def test_error_vectorial_pequeno_conserva_mensaje_exacto():
    """Las celdas dentro del límite conservan su diagnóstico original."""
    carga = {"scalar": "2", "v": {"orientation": "column", "data": ["abc"]}}
    respuesta = json.loads(ControladorOperacionesVectores.procesar_multiplicacion_escalar(json.dumps(carga)))
    assert respuesta == {"status": "ERROR", "message": "Valor inválido: abc. El valor ingresado no es un número o fracción válida."}
