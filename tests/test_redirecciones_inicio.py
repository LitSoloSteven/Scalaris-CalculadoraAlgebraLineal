from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.frontend import navegacion
from src.frontend.rutas import registrar_redirecciones_heredadas
from tests.comun_clientes import crear_cliente_redirecciones
from tests.comun_redirecciones import REDIRECCIONES_ESPERADAS


@pytest.fixture
def cliente_inicio(monkeypatch):
    """Crea un cliente de redirecciones con el inicio habilitado."""
    monkeypatch.setattr(navegacion, "INICIO_HABILITADO", True)
    return crear_cliente_redirecciones()


def test_rutas_heredadas_redirigen_permanentemente_con_inicio(cliente_inicio):
    """Verifica que con inicio activo, todas las rutas heredadas devuelvan 301 con Location correcto."""
    for ruta, ubicacion_esperada in REDIRECCIONES_ESPERADAS.items():
        respuesta = cliente_inicio.get(ruta)
        assert respuesta.status_code == 301, f"Ruta {ruta} devolvió {respuesta.status_code}, se esperaba 301"
        assert respuesta.headers["location"] == ubicacion_esperada


def test_parametros_consultas_conservados_y_precedencia(cliente_inicio):
    """Verifica que la consulta se preserve con 301 y que la fija tenga precedencia."""
    respuesta_primera = cliente_inicio.get("/matriz-inversa?foo=bar&baz=1")
    assert respuesta_primera.status_code == 301
    assert respuesta_primera.headers["location"] == "/algebra-lineal/inversa?foo=bar&baz=1"

    respuesta_segunda = cliente_inicio.get("/gauss?extra=test")
    assert respuesta_segunda.status_code == 301
    assert respuesta_segunda.headers["location"] == "/algebra-lineal/sistemas?method=gauss&extra=test"

    respuesta_tercera = cliente_inicio.get("/gauss?method=override")
    assert respuesta_tercera.status_code == 301
    assert respuesta_tercera.headers["location"] == "/algebra-lineal/sistemas?method=gauss"


def test_redirecciones_inicio_sin_cadenas(cliente_inicio):
    """Verifica que no haya cadenas de redirecciones hacia otras rutas heredadas."""
    rutas_heredadas = {regla.ruta for regla in navegacion.redirecciones_heredadas()}
    for ruta in rutas_heredadas:
        respuesta = cliente_inicio.get(ruta)
        destino = respuesta.headers["location"].split("?")[0]
        assert destino not in rutas_heredadas, f"Cadena detectada: {ruta} -> {destino}"


def test_inicio_desactivado_redirige_temporalmente(monkeypatch):
    """Verifica que con inicio desactivado, las rutas que dependen del indicador devuelvan 302."""
    monkeypatch.setattr(navegacion, "INICIO_HABILITADO", False)
    cliente = crear_cliente_redirecciones()

    for ruta in ("/", "/ia"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 302, f"Ruta {ruta} devolvió {respuesta.status_code}, se esperaba 302"
        assert respuesta.headers["location"] == "/algebra-lineal/sistemas"
