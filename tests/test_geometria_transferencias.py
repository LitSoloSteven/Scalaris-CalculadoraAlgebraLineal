"""Pruebas de transferencia de datos de geometria (sistemas, vectores y matrices)."""
from unittest.mock import patch
from tests.comun import limpiar_almacen_transferencia

from src.frontend.componentes.transferencia import (
    ResultadoTransferencia,
    TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS,
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
    limpiar_almacen_transferencia()
    token = guardar_sistema("sistemas", [["1", "2"], ["3", "4"]], ["5", "6"])
    resultado = consumir_sistema(token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    assert resultado.estado == "exito"
    assert resultado.datos["matriz_a"] == [["1", "2"], ["3", "4"]]
    assert resultado.datos["vector_b"] == ["5", "6"]


def test_sistema_se_consume_una_sola_vez():
    """El segundo consumo informa que la transferencia ya no existe."""
    limpiar_almacen_transferencia()
    token = guardar_sistema("sistemas", [["1", "1"]], ["2"])
    resultado_primero = consumir_sistema(token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    assert resultado_primero.estado == "exito"
    resultado_segundo = consumir_sistema(token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    assert resultado_segundo.estado == "ausente"


def test_consumir_sistema_vencido():
    """El sistema vencido devuelve el estado de expiración."""
    limpiar_almacen_transferencia()
    token = guardar_sistema("test", [["1", "1"]], ["2"])
    with patch("src.frontend.componentes.transferencia._ahora", return_value=_ahora() + TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS + 10):
        resultado = consumir_sistema(token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    assert resultado.estado == "expirada"


def test_consumir_sistema_con_token_vacio():
    """Un token vacío devuelve la ausencia de transferencia."""
    resultado = consumir_sistema("", maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    assert resultado is None


def test_sistema_rechaza_dimension_invalida():
    """La transferencia rechaza una dimensión no admitida por el destino."""
    limpiar_almacen_transferencia()
    token = guardar_sistema("test", [["1", "0", "0", "0"]], ["1"])
    resultado = consumir_sistema(token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    assert resultado.estado == "invalida"


def test_sistema_rechaza_celdas_invalidas():
    """El sistema con una celda no numérica devuelve estado inválido."""
    limpiar_almacen_transferencia()
    token = guardar_sistema("test", [["abc", "1"]], ["1"])
    resultado = consumir_sistema(token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    assert resultado.estado == "invalida"


def test_guardar_y_consumir_vectores_exitoso():
    """La transferencia conserva la escena y los datos de vectores."""
    limpiar_almacen_transferencia()
    token = guardar_vectores("vectores", "vectores", [["1", "2"], ["3", "4"]])
    resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})
    assert resultado.estado == "exito"
    assert resultado.datos["escena"] == "vectores"
    assert resultado.datos["vectores"] == [["1", "2"], ["3", "4"]]


def test_vectores_se_consumen_una_sola_vez():
    """El segundo consumo informa ausencia de vectores transferidos."""
    limpiar_almacen_transferencia()
    token = guardar_vectores("vectores", "combinacion", [["1", "2"]])
    resultado_primero = consumir_vectores(token, dimensiones_permitidas={2, 3})
    assert resultado_primero.estado == "exito"
    resultado_segundo = consumir_vectores(token, dimensiones_permitidas={2, 3})
    assert resultado_segundo.estado == "ausente"


def test_consumir_vectores_vencidos():
    """Los vectores vencidos devuelven el estado de expiración."""
    limpiar_almacen_transferencia()
    token = guardar_vectores("test", "vectores", [["1", "0"]])
    with patch("src.frontend.componentes.transferencia._ahora", return_value=_ahora() + TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS + 10):
        resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})
    assert resultado.estado == "expirada"


def test_vectores_rechazan_dimension_invalida():
    """El destino rechaza vectores de una dimensión no admitida."""
    limpiar_almacen_transferencia()
    token = guardar_vectores("test", "vectores", [["1", "0", "0", "0"]])
    resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})
    assert resultado.estado == "invalida"


def test_vectores_rechazan_celdas_invalidas():
    """El vector con una celda no numérica devuelve estado inválido."""
    limpiar_almacen_transferencia()
    token = guardar_vectores("test", "vectores", [["abc", "1"]])
    resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})
    assert resultado.estado == "invalida"


def test_guardar_y_consumir_matriz():
    """Garantiza funcionamiento de guardar_matriz y consumir_matriz."""
    limpiar_almacen_transferencia()
    token = guardar_matriz("sistemas", [["1", "2"], ["3", "4"]])
    resultado = consumir_matriz(token, dimension_maxima=10)
    assert resultado.estado == "exito"
    assert resultado.datos == [["1", "2"], ["3", "4"]]


def test_modulo_transferencias_exporta_funciones():
    """Verifica la exportacion del modulo handoff con funciones en espanol."""
    import src.frontend.componentes.transferencia
    assert hasattr(src.frontend.componentes.transferencia, "guardar_sistema")
    assert hasattr(src.frontend.componentes.transferencia, "consumir_sistema")
    assert hasattr(src.frontend.componentes.transferencia, "guardar_vectores")
    assert hasattr(src.frontend.componentes.transferencia, "consumir_vectores")
