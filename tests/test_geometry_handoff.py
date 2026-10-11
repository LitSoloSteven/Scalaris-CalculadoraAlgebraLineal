"""Pruebas de transferencia de datos de geometria (sistemas, vectores y matrices)."""
from unittest.mock import patch

from src.frontend.componentes.handoff import (
    ResultadoHandoff,
    TTL_SEGUNDOS,
    _ALMACEN,
    consumir_matriz,
    consumir_sistema,
    consumir_vectores,
    guardar_matriz,
    guardar_sistema,
    guardar_vectores,
    _ahora,
)


def _limpiar_almacen():
    _ALMACEN.clear()


def test_put_consume_system_ok():
    _limpiar_almacen()
    token = guardar_sistema("sistemas", [["1", "2"], ["3", "4"]], ["5", "6"])
    result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "ok"
    assert result.data["matrix_A"] == [["1", "2"], ["3", "4"]]
    assert result.data["vector_b"] == ["5", "6"]


def test_put_consume_system_single_use():
    _limpiar_almacen()
    token = guardar_sistema("sistemas", [["1", "1"]], ["2"])
    result1 = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result1.status == "ok"
    result2 = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result2.status == "missing"


def test_consume_system_expired():
    _limpiar_almacen()
    token = guardar_sistema("test", [["1", "1"]], ["2"])
    with patch("src.frontend.componentes.handoff._ahora", return_value=_ahora() + TTL_SEGUNDOS + 10):
        result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "expired"


def test_consume_system_empty_token():
    result = consumir_sistema("", max_m=10, allowed_n={2, 3})
    assert result is None


def test_system_invalid_n():
    _limpiar_almacen()
    token = guardar_sistema("test", [["1", "0", "0", "0"]], ["1"])
    result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "invalid"


def test_system_invalid_cells():
    _limpiar_almacen()
    token = guardar_sistema("test", [["abc", "1"]], ["1"])
    result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "invalid"


def test_put_consume_vectors_ok():
    _limpiar_almacen()
    token = guardar_vectores("vectores", "vectores", [["1", "2"], ["3", "4"]])
    result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "ok"
    assert result.data["scene"] == "vectores"
    assert result.data["data"] == [["1", "2"], ["3", "4"]]


def test_put_consume_vectors_single_use():
    _limpiar_almacen()
    token = guardar_vectores("vectores", "combinacion", [["1", "2"]])
    result1 = consumir_vectores(token, allowed_n={2, 3})
    assert result1.status == "ok"
    result2 = consumir_vectores(token, allowed_n={2, 3})
    assert result2.status == "missing"


def test_consume_vectors_expired():
    _limpiar_almacen()
    token = guardar_vectores("test", "vectores", [["1", "0"]])
    with patch("src.frontend.componentes.handoff._ahora", return_value=_ahora() + TTL_SEGUNDOS + 10):
        result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "expired"


def test_vectors_invalid_dimension():
    _limpiar_almacen()
    token = guardar_vectores("test", "vectores", [["1", "0", "0", "0"]])
    result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "invalid"


def test_vectors_invalid_cells():
    _limpiar_almacen()
    token = guardar_vectores("test", "vectores", [["abc", "1"]])
    result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "invalid"


def test_put_matrix_consume_matrix_still_work():
    """Garantiza funcionamiento de guardar_matriz y consumir_matriz."""
    _limpiar_almacen()
    token = guardar_matriz("sistemas", [["1", "2"], ["3", "4"]])
    result = consumir_matriz(token, max_n=10)
    assert result.status == "ok"
    assert result.data == [["1", "2"], ["3", "4"]]


def test_handoff_module_imports():
    """Verifica la exportacion del modulo handoff con funciones en espanol."""
    import src.frontend.componentes.handoff
    assert hasattr(src.frontend.componentes.handoff, "guardar_sistema")
    assert hasattr(src.frontend.componentes.handoff, "consumir_sistema")
    assert hasattr(src.frontend.componentes.handoff, "guardar_vectores")
    assert hasattr(src.frontend.componentes.handoff, "consumir_vectores")
