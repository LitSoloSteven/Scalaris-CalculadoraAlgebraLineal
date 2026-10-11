from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.frontend import navigation
from src.frontend.routes import registrar_redirecciones_legacy
from tests.comun_clientes import crear_cliente_redirecciones


@pytest.fixture
def cliente_hub(monkeypatch):
    """Crea un cliente de redirecciones con el Hub habilitado."""
    monkeypatch.setattr(navigation, "HUB_ENABLED", True)
    return crear_cliente_redirecciones()


def test_rutas_heredadas_redirigen_permanentemente_con_hub(cliente_hub):
    """Verifica que con Hub activo, todas las rutas legacy devuelvan 301 con Location correcto."""
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

    for path, expected_loc in expected_redirects.items():
        resp = cliente_hub.get(path)
        assert resp.status_code == 301, f"Ruta {path} devolvió {resp.status_code}, se esperaba 301"
        assert resp.headers["location"] == expected_loc


def test_parametros_consultas_conservados_y_precedencia(cliente_hub):
    """Verifica que la query se preserve con 301 y que la fija tenga precedencia."""
    r1 = cliente_hub.get("/matriz-inversa?foo=bar&baz=1")
    assert r1.status_code == 301
    assert r1.headers["location"] == "/algebra-lineal/inversa?foo=bar&baz=1"

    r2 = cliente_hub.get("/gauss?extra=test")
    assert r2.status_code == 301
    assert r2.headers["location"] == "/algebra-lineal/sistemas?method=gauss&extra=test"

    r3 = cliente_hub.get("/gauss?method=override")
    assert r3.status_code == 301
    assert r3.headers["location"] == "/algebra-lineal/sistemas?method=gauss"


def test_redirecciones_hub_sin_cadenas(cliente_hub):
    """Verifica que no haya cadenas de redirecciones hacia otras rutas legacy."""
    legacy_paths = {rule.path for rule in navigation.legacy_redirects()}
    for path in legacy_paths:
        resp = cliente_hub.get(path)
        target = resp.headers["location"].split("?")[0]
        assert target not in legacy_paths, f"Cadena detectada: {path} -> {target}"


def test_hub_desactivado_redirige_temporalmente(monkeypatch):
    """Verifica que con Hub desactivado, las rutas que dependen del flag devuelvan 302."""
    monkeypatch.setattr(navigation, "HUB_ENABLED", False)
    client = crear_cliente_redirecciones()

    for path in ("/", "/ia"):
        resp = client.get(path)
        assert resp.status_code == 302, f"Ruta {path} devolvió {resp.status_code}, se esperaba 302"
        assert resp.headers["location"] == "/algebra-lineal/sistemas"
