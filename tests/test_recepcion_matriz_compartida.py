"""Recepción de matrices, aislamiento de capturas y consumo único del token."""
from unittest.mock import MagicMock, Mock
import pytest

from src.frontend.componentes import transferencia
from src.frontend.constantes import TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS


def _preparar(monkeypatch):
    aviso, limpiar, cargar = Mock(), Mock(), Mock()
    monkeypatch.setattr(transferencia, "renderizar_aviso_transferencia", aviso)
    monkeypatch.setattr(transferencia, "limpiar_url_transferencia", limpiar)
    return aviso, limpiar, cargar


def test_recepcion_exacta_consumible_una_vez_y_almacen_independiente(monkeypatch):
    """La matriz guardada conserva fracciones aunque el productor modifique su lista."""
    aviso, limpiar, cargar = _preparar(monkeypatch)
    datos = [["1/1001", "-2/3"], ["0", "1"]]
    token = transferencia.guardar_matriz("determinantes", datos)
    datos[0][0] = "99"
    resultado = transferencia.recibir_matriz(token, "inversa", cargar, MagicMock())
    esperado = [["1/1001", "-2/3"], ["0", "1"]]
    cargar.assert_called_once_with(esperado)
    assert resultado.estado == "exito" and resultado.datos == esperado
    assert "2×2" in aviso.call_args.args[1] and "Determinantes" in aviso.call_args.args[1]
    assert transferencia.consumir_matriz(token, dimension_maxima=50).estado == "ausente"
    limpiar.assert_called_once_with()


@pytest.mark.parametrize("destino,datos", [
    ("inversa", [["1", "2"]]), ("determinantes", [["1/0"]]),
    ("leontief", [["1"]]), ("transformaciones", [["1"] * 9 for _ in range(9)]),
    ("factorizacion_lu", [["1"] * 11 for _ in range(11)]),
    ("sistemas", [["1", "0"], ["0"]]),
])
def test_rechazo_no_invoca_cargador_y_limpia_url(monkeypatch, destino, datos):
    """Estructura, sintaxis y límites se validan antes de modificar el panel."""
    aviso, limpiar, cargar = _preparar(monkeypatch)
    token = transferencia.guardar_matriz("matrices", datos)
    resultado = transferencia.recibir_matriz(token, destino, cargar, MagicMock())
    assert resultado.estado == "invalida" and resultado.datos is None
    assert resultado.mensaje
    cargar.assert_not_called()
    aviso.assert_called_once_with(resultado, "")
    limpiar.assert_called_once_with()


def test_ausencia_no_muestra_aviso_ni_limpia_url(monkeypatch):
    """La carga normal sin token no altera el estado ni programa trabajo cliente."""
    aviso, limpiar, cargar = _preparar(monkeypatch)
    assert transferencia.recibir_matriz("", "matrices", cargar, MagicMock()) is None
    aviso.assert_not_called()
    limpiar.assert_not_called()
    cargar.assert_not_called()


@pytest.mark.parametrize("expirada", [False, True])
def test_token_inexistente_o_expirado_conserva_panel(monkeypatch, expirada):
    """Las transferencias no reutilizables informan y limpian el parámetro URL."""
    aviso, limpiar, cargar = _preparar(monkeypatch)
    token = "token-ausente"
    if expirada:
        token = transferencia.guardar_matriz("sistemas", [["1"]])
        hora = transferencia._ahora()
        monkeypatch.setattr(transferencia, "_ahora", lambda: hora + TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS + 1)
    resultado = transferencia.recibir_matriz(token, "inversa", cargar, MagicMock())
    assert resultado.estado == ("expirada" if expirada else "ausente")
    cargar.assert_not_called()
    limpiar.assert_called_once_with()
    aviso.assert_called_once_with(resultado, "")


def test_error_del_panel_no_publica_exito_y_retira_token(monkeypatch):
    """Un cargador defectuoso propaga el error sin conservar un enlace consumido."""
    aviso, limpiar, cargar = _preparar(monkeypatch)
    cargar.side_effect = RuntimeError("fallo simulado")
    token = transferencia.guardar_matriz("matrices", [["1"]])
    with pytest.raises(RuntimeError, match="fallo simulado"):
        transferencia.recibir_matriz(token, "inversa", cargar, MagicMock())
    aviso.assert_not_called()
    limpiar.assert_called_once_with()
