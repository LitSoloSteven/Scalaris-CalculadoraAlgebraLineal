"""Configuración del secreto de almacenamiento por entorno de ejecución."""
import pytest
from src.frontend.aplicacion import resolver_secreto_almacenamiento


def test_secreto_almacenamiento_desarrollo():
    """Desarrollo conserva el secreto predeterminado esperado."""
    env = {"SCALARIS_ENV": "development"}
    assert resolver_secreto_almacenamiento(env) == "scalaris_dev_secret_key"


def test_secreto_almacenamiento_produccion_ausente():
    """Producción exige el secreto y termina si no está configurado."""
    env = {"SCALARIS_ENV": "production"}
    with pytest.raises(SystemExit):
        resolver_secreto_almacenamiento(env)


def test_secreto_almacenamiento_produccion_presente():
    """Producción usa el valor configurado del secreto."""
    env = {"SCALARIS_ENV": "production", "STORAGE_SECRET": "my_secret"}
    assert resolver_secreto_almacenamiento(env) == "my_secret"
