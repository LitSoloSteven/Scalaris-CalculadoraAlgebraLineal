"""Pruebas de transferencia de datos de geometria (sistemas, vectores y matrices)."""
from unittest.mock import patch
from tests.comun import limpiar_almacen_handoff

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


def test_guardar_y_consumir_sistema_exitoso():
    """La transferencia conserva coeficientes y términos independientes."""
    limpiar_almacen_handoff()
    token = guardar_sistema("sistemas", [["1", "2"], ["3", "4"]], ["5", "6"])
    result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "ok"
    assert result.data["matrix_A"] == [["1", "2"], ["3", "4"]]
    assert result.data["vector_b"] == ["5", "6"]


def test_sistema_se_consume_una_sola_vez():
    """El segundo consumo informa que la transferencia ya no existe."""
    limpiar_almacen_handoff()
    token = guardar_sistema("sistemas", [["1", "1"]], ["2"])
    result1 = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result1.status == "ok"
    result2 = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result2.status == "missing"


def test_consumir_sistema_vencido():
    """El sistema vencido devuelve el estado de expiración."""
    limpiar_almacen_handoff()
    token = guardar_sistema("test", [["1", "1"]], ["2"])
    with patch("src.frontend.componentes.handoff._ahora", return_value=_ahora() + TTL_SEGUNDOS + 10):
        result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "expired"


def test_consumir_sistema_con_token_vacio():
    """Un token vacío devuelve la ausencia de transferencia."""
    result = consumir_sistema("", max_m=10, allowed_n={2, 3})
    assert result is None


def test_sistema_rechaza_dimension_invalida():
    """La transferencia rechaza una dimensión no admitida por el destino."""
    limpiar_almacen_handoff()
    token = guardar_sistema("test", [["1", "0", "0", "0"]], ["1"])
    result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "invalid"


def test_sistema_rechaza_celdas_invalidas():
    """El sistema con una celda no numérica devuelve estado inválido."""
    limpiar_almacen_handoff()
    token = guardar_sistema("test", [["abc", "1"]], ["1"])
    result = consumir_sistema(token, max_m=10, allowed_n={2, 3})
    assert result.status == "invalid"


def test_guardar_y_consumir_vectores_exitoso():
    """La transferencia conserva la escena y los datos de vectores."""
    limpiar_almacen_handoff()
    token = guardar_vectores("vectores", "vectores", [["1", "2"], ["3", "4"]])
    result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "ok"
    assert result.data["scene"] == "vectores"
    assert result.data["data"] == [["1", "2"], ["3", "4"]]


def test_vectores_se_consumen_una_sola_vez():
    """El segundo consumo informa ausencia de vectores transferidos."""
    limpiar_almacen_handoff()
    token = guardar_vectores("vectores", "combinacion", [["1", "2"]])
    result1 = consumir_vectores(token, allowed_n={2, 3})
    assert result1.status == "ok"
    result2 = consumir_vectores(token, allowed_n={2, 3})
    assert result2.status == "missing"


def test_consumir_vectores_vencidos():
    """Los vectores vencidos devuelven el estado de expiración."""
    limpiar_almacen_handoff()
    token = guardar_vectores("test", "vectores", [["1", "0"]])
    with patch("src.frontend.componentes.handoff._ahora", return_value=_ahora() + TTL_SEGUNDOS + 10):
        result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "expired"


def test_vectores_rechazan_dimension_invalida():
    """El destino rechaza vectores de una dimensión no admitida."""
    limpiar_almacen_handoff()
    token = guardar_vectores("test", "vectores", [["1", "0", "0", "0"]])
    result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "invalid"


def test_vectores_rechazan_celdas_invalidas():
    """El vector con una celda no numérica devuelve estado inválido."""
    limpiar_almacen_handoff()
    token = guardar_vectores("test", "vectores", [["abc", "1"]])
    result = consumir_vectores(token, allowed_n={2, 3})
    assert result.status == "invalid"


def test_guardar_y_consumir_matriz():
    """Garantiza funcionamiento de guardar_matriz y consumir_matriz."""
    limpiar_almacen_handoff()
    token = guardar_matriz("sistemas", [["1", "2"], ["3", "4"]])
    result = consumir_matriz(token, max_n=10)
    assert result.status == "ok"
    assert result.data == [["1", "2"], ["3", "4"]]


def test_modulo_transferencias_exporta_funciones():
    """Verifica la exportacion del modulo handoff con funciones en espanol."""
    import src.frontend.componentes.handoff
    assert hasattr(src.frontend.componentes.handoff, "guardar_sistema")
    assert hasattr(src.frontend.componentes.handoff, "consumir_sistema")
    assert hasattr(src.frontend.componentes.handoff, "guardar_vectores")
    assert hasattr(src.frontend.componentes.handoff, "consumir_vectores")
