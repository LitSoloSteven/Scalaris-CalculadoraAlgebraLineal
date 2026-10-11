"""Redirecciones heredadas, parámetros de consulta y estado del Hub."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.frontend import navigation
from src.frontend.routes import registrar_redirecciones_legacy
from tests.comun_clientes import crear_cliente_redirecciones


@pytest.fixture
def cliente():
    """Crea una aplicación FastAPI mínima con las redirecciones legacy registradas."""
    return crear_cliente_redirecciones()


def test_rutas_heredadas_con_hub_estado_y_destino(cliente):
    """Las rutas heredadas conservan el código 301 y su destino exacto."""
    expected_redirects = {
        "/ia": "/?glosa=1",
        "/sistemas-lineales": "/algebra-lineal/sistemas",
        "/gauss": "/algebra-lineal/sistemas?method=gauss",
        "/gauss-jordan": "/algebra-lineal/sistemas?method=gauss-jordan",
        "/operaciones-matrices": "/algebra-lineal/matrices",
        "/matriz-inversa": "/algebra-lineal/inversa",
        "/vectores": "/algebra-lineal/vectores",
        "/conversor": "/utilidades/bases",
        "/romanos": "/utilidades/romanos",
    }

    for path, expected_location in expected_redirects.items():
        response = cliente.get(path)
        assert response.status_code == 301, f"Ruta {path} devolvió código {response.status_code}, se esperaba 301"
        assert response.headers["location"] == expected_location, (
            f"Ruta {path} redirigió a {response.headers['location']}, se esperaba {expected_location}"
        )


def test_rutas_heredadas_sin_hub(monkeypatch):
    """Verifica que con HUB_ENABLED=False, '/' y '/ia' redirijan a /algebra-lineal/sistemas con 302."""
    monkeypatch.setattr(navigation, "HUB_ENABLED", False)
    c = crear_cliente_redirecciones()

    for path in ("/", "/ia"):
        resp = c.get(path)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/algebra-lineal/sistemas"


def test_conservacion_consultas_y_precedencia(cliente):
    """Verifica la preservación de parámetros query y la precedencia de queries fijas."""
    r1 = cliente.get("/sistemas-lineales?method=gauss-jordan")
    assert r1.status_code == 301
    assert r1.headers["location"] == "/algebra-lineal/sistemas?method=gauss-jordan"

    r2 = cliente.get("/gauss?x=1")
    assert r2.status_code == 301
    assert r2.headers["location"] == "/algebra-lineal/sistemas?method=gauss&x=1"

    r3 = cliente.get("/gauss?method=gauss-jordan")
    assert r3.status_code == 301
    assert r3.headers["location"] == "/algebra-lineal/sistemas?method=gauss"


def test_rutas_heredadas_sin_cadenas(cliente):
    """Confirma que ningún Location de redirección apunte a otra ruta legacy."""
    legacy_paths = {rule.path for rule in navigation.legacy_redirects()}

    for path in legacy_paths:
        resp = cliente.get(path)
        target_path = resp.headers["location"].split("?")[0]
        assert target_path not in legacy_paths, (
            f"Ruta {path} produce una cadena redirigiendo a otra ruta legacy: {target_path}"
        )


def test_redirecciones_con_hub_habilitado(monkeypatch):
    """Valida el comportamiento con HUB_ENABLED=True: '/' no se registra e '/ia' va a '/?glosa=1'."""
    monkeypatch.setattr(navigation, "HUB_ENABLED", True)

    hub_client = crear_cliente_redirecciones()

    r_root = hub_client.get("/")
    assert r_root.status_code == 404, "Con HUB_ENABLED=True, '/' no debe ser manejado por legacy_redirects"

    r_ia = hub_client.get("/ia")
    assert r_ia.status_code == 301
    assert r_ia.headers["location"] == "/?glosa=1"
