"""Compatibilidad por eje y recepción diferenciada de matrices rectangulares."""
from unittest.mock import MagicMock, Mock
import pytest

from src.frontend.componentes import transferencia
from src.frontend.controladores.destinos_matriz import destinos_compatibles

DESTINOS_RECTANGULARES = {"factorizacion_lu", "sistemas", "matrices", "transformaciones"}


@pytest.mark.parametrize("filas,columnas,esperados", [
    (2, 3, DESTINOS_RECTANGULARES), (3, 2, DESTINOS_RECTANGULARES),
    (1, 8, DESTINOS_RECTANGULARES), (8, 1, DESTINOS_RECTANGULARES),
    (8, 9, DESTINOS_RECTANGULARES - {"transformaciones"}),
    (9, 8, DESTINOS_RECTANGULARES - {"transformaciones"}),
    (1, 10, DESTINOS_RECTANGULARES - {"transformaciones"}),
    (10, 1, DESTINOS_RECTANGULARES - {"transformaciones"}),
    (1, 11, set()), (11, 1, set()), (2, 0, set()), (0, 2, set()),
])
def test_destinos_rectangulares_respetan_ambos_ejes(filas, columnas, esperados):
    """Cada eje debe caber y los destinos cuadrados nunca reciben rectángulos."""
    assert set(destinos_compatibles(filas, columnas, "")) == esperados


@pytest.mark.parametrize("origen", sorted(DESTINOS_RECTANGULARES))
def test_rectangulo_excluye_solo_el_origen_compatible(origen):
    """La transferencia entre herramientas rectangulares conserva otros destinos."""
    assert set(destinos_compatibles(2, 3, origen)) == DESTINOS_RECTANGULARES - {origen}
    assert destinos_compatibles(2, 3, "vectores") == ()


@pytest.mark.parametrize("destino", sorted(DESTINOS_RECTANGULARES))
def test_recepcion_rectangular_delega_valida_y_limpia_url(monkeypatch, destino):
    """Los cuatro receptores cargan la matriz exacta mediante el flujo común."""
    aviso, limpiar, cargar = Mock(), Mock(), Mock()
    monkeypatch.setattr(transferencia, "renderizar_aviso_transferencia", aviso)
    monkeypatch.setattr(transferencia, "limpiar_url_transferencia", limpiar)
    datos = [["1/1001", "0", "-2/3"], ["4", "5.00", "6"]]
    token = transferencia.guardar_matriz("matrices", datos)
    resultado = transferencia.recibir_matriz(token, destino, cargar, MagicMock())
    assert resultado.estado == "exito" and resultado.datos == datos
    cargar.assert_called_once_with(datos)
    assert "2×3" in aviso.call_args.args[1]
    limpiar.assert_called_once_with()
    assert transferencia.consumir_matriz_rectangular(token, filas_maximas=2, columnas_maximas=3).estado == "ausente"


@pytest.mark.parametrize("destino", ["inversa", "determinantes", "leontief"])
def test_destinos_cuadrados_rechazan_rectangulos_sin_cargar(monkeypatch, destino):
    """El nuevo consumidor no amplía las formas admitidas por herramientas cuadradas."""
    limpiar, cargar = Mock(), Mock()
    monkeypatch.setattr(transferencia, "limpiar_url_transferencia", limpiar)
    monkeypatch.setattr(transferencia, "renderizar_aviso_transferencia", Mock())
    token = transferencia.guardar_matriz("factorizacion_lu", [["1", "2", "3"], ["4", "5", "6"]])
    assert transferencia.recibir_matriz(token, destino, cargar, MagicMock()).estado == "invalida"
    cargar.assert_not_called()
    limpiar.assert_called_once_with()


def test_consumidor_rectangular_conserva_copia_y_maximos_asimetricos():
    """El sobre mantiene datos independientes y permite límites distintos por eje."""
    datos = [["1", "2", "3"], ["4", "5", "6"]]
    token = transferencia.guardar_matriz("matrices", datos)
    datos[0][0] = "99"
    carga = transferencia.consumir_matriz_rectangular(token, filas_maximas=2, columnas_maximas=3)
    assert carga.estado == "exito" and carga.datos == [["1", "2", "3"], ["4", "5", "6"]]


@pytest.mark.parametrize("filas,columnas", [(11, 2), (2, 11)])
def test_rectangulo_excesivo_no_carga_ni_recorta(monkeypatch, filas, columnas):
    """El receptor rechaza el exceso en cualquiera de sus ejes antes de cargar."""
    cargar = Mock()
    monkeypatch.setattr(transferencia, "limpiar_url_transferencia", Mock())
    monkeypatch.setattr(transferencia, "renderizar_aviso_transferencia", Mock())
    token = transferencia.guardar_matriz("matrices", [["1"] * columnas for _ in range(filas)])
    resultado = transferencia.recibir_matriz(token, "factorizacion_lu", cargar, MagicMock())
    assert resultado.estado == "invalida" and f"{filas}×{columnas}" in resultado.mensaje
    cargar.assert_not_called()
