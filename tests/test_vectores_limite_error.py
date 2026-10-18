"""Límite de presentación de errores para celdas vectoriales excesivas."""
import json

from src.frontend.controladores.operaciones_vectores import ControladorOperacionesVectores


def test_error_vectorial_no_refleja_celda_excesiva():
    """El parser rechaza una celda grande sin repetir su contenido completo en la respuesta."""
    carga = {"escalar": "2", "vector": {"orientacion": "columna", "datos": ["9" * 100000]}}
    respuesta = ControladorOperacionesVectores.procesar_multiplicacion_escalar(json.dumps(carga))
    assert json.loads(respuesta)["estado"] == "ERROR"
    assert len(respuesta) < 300


def test_error_vectorial_pequeno_conserva_mensaje_exacto():
    """Las celdas dentro del límite conservan su diagnóstico original."""
    carga = {"escalar": "2", "vector": {"orientacion": "columna", "datos": ["abc"]}}
    respuesta = json.loads(ControladorOperacionesVectores.procesar_multiplicacion_escalar(json.dumps(carga)))
    assert respuesta == {"estado": "ERROR", "mensaje": "Valor inválido: abc. El valor ingresado no es un número o fracción válida."}
