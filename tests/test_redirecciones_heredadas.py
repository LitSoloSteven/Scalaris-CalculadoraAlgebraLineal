"""Redirecciones heredadas, parámetros de consulta y estado del inicio."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.frontend import navegacion
from src.frontend.rutas import registrar_redirecciones_heredadas
from tests.comun_clientes import crear_cliente_redirecciones
from tests.comun_redirecciones import REDIRECCIONES_ESPERADAS


@pytest.fixture
def cliente():
    """Crea una aplicación FastAPI mínima con las redirecciones heredadas registradas."""
    return crear_cliente_redirecciones()


def test_rutas_heredadas_con_inicio_estado_y_destino(cliente):
    """Las rutas heredadas conservan el código 301 y su destino exacto."""
    for ruta, ubicacion_esperada in REDIRECCIONES_ESPERADAS.items():
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 301, f"Ruta {ruta} devolvió código {respuesta.status_code}, se esperaba 301"
        assert respuesta.headers["location"] == ubicacion_esperada, (
            f"Ruta {ruta} redirigió a {respuesta.headers['location']}, se esperaba {ubicacion_esperada}"
        )


def test_rutas_heredadas_sin_inicio(monkeypatch):
    """Verifica que con INICIO_HABILITADO=False, '/' y '/ia' redirijan a /algebra-lineal/sistemas con 302."""
    monkeypatch.setattr(navegacion, "INICIO_HABILITADO", False)
    c = crear_cliente_redirecciones()

    for ruta in ("/", "/ia"):
        respuesta = c.get(ruta)
        assert respuesta.status_code == 302
        assert respuesta.headers["location"] == "/algebra-lineal/sistemas"


def test_conservacion_consultas_y_precedencia(cliente):
    """Verifica la preservación de parámetros consulta y la precedencia de consultas fijas."""
    respuesta_primera = cliente.get("/sistemas-lineales?method=gauss-jordan")
    assert respuesta_primera.status_code == 301
    assert respuesta_primera.headers["location"] == "/algebra-lineal/sistemas?method=gauss-jordan"

    respuesta_segunda = cliente.get("/gauss?x=1")
    assert respuesta_segunda.status_code == 301
    assert respuesta_segunda.headers["location"] == "/algebra-lineal/sistemas?method=gauss&x=1"

    respuesta_tercera = cliente.get("/gauss?method=gauss-jordan")
    assert respuesta_tercera.status_code == 301
    assert respuesta_tercera.headers["location"] == "/algebra-lineal/sistemas?method=gauss"


def test_rutas_heredadas_sin_cadenas(cliente):
    """Confirma que ningún Location de redirección apunte a otra ruta heredadas."""
    rutas_heredadas = {regla.ruta for regla in navegacion.redirecciones_heredadas()}

    for ruta in rutas_heredadas:
        respuesta = cliente.get(ruta)
        ruta_destino = respuesta.headers["location"].split("?")[0]
        assert ruta_destino not in rutas_heredadas, (
            f"Ruta {ruta} produce una cadena redirigiendo a otra ruta legacy: {ruta_destino}"
        )


def test_redirecciones_con_inicio_habilitado(monkeypatch):
    """Valida el comportamiento con INICIO_HABILITADO=verdadero: '/' no se registra e '/ia' va a '/?glosa=1'."""
    monkeypatch.setattr(navegacion, "INICIO_HABILITADO", True)

    cliente_inicio = crear_cliente_redirecciones()

    respuesta_raiz = cliente_inicio.get("/")
    assert respuesta_raiz.status_code == 404, "Con INICIO_HABILITADO=True, '/' no debe ser manejado por redirecciones_heredadas"

    respuesta_ia = cliente_inicio.get("/ia")
    assert respuesta_ia.status_code == 301
    assert respuesta_ia.headers["location"] == "/?glosa=1"
