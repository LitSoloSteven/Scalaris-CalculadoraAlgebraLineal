"""Rechazo de la muestra textual inválida del controlador inverso."""
from src.frontend.controladores.operaciones_inversas import ControladorOperacionesInversas


def test_inversa_rechaza_texto_que_no_es_json():
    """La muestra textual conserva el error estructurado sin acceder al cálculo."""
    resultado = ControladorOperacionesInversas.procesar_inversa("esto no es json")
    assert resultado["estado"] == "ERROR"
