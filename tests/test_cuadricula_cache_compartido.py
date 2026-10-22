"""Caracterización del caché compartido por los componentes de captura."""
from types import SimpleNamespace
from unittest.mock import Mock

from src.frontend.componentes.cuadricula_base import (
    cache_matriz_desde_datos, deshabilitar_botones_dimension, sincronizar_cache_celdas,
)
from src.backend.constantes import DIMENSION_MAXIMA_INVERSA
from src.frontend.componentes.panel_matriz_cuadrada import PanelMatrizCuadrada


def test_cache_de_carga_conserva_texto_y_omite_ceros_sin_parsear():
    """La captura preserva fracciones y texto inválido sin anticipar la validación."""
    datos = [["0", " 1/1001 ", "", "-2/3"], ["invalido", " 0 ", "  "]]
    assert cache_matriz_desde_datos(datos) == {
        (0, 1): "1/1001", (0, 3): "-2/3", (1, 0): "invalido",
    }


def test_sincronizacion_conserva_el_cache_previo_y_copia_ceros_textuales():
    """Los valores vacíos no sobrescriben el caché mientras los ceros sí se copian."""
    cache = {(0, 0): "anterior", (1, 0): "fuera"}
    entradas = [[SimpleNamespace(value=""), SimpleNamespace(value="0"), SimpleNamespace(value="1/3")]]
    sincronizar_cache_celdas(entradas, cache)
    assert cache == {(0, 0): "anterior", (1, 0): "fuera", (0, 1): "0", (0, 2): "1/3"}


def test_controles_ausentes_no_impiden_deshabilitar_los_presentes():
    """Todos los botones montados se deshabilitan una vez, sin exigir los demás."""
    primero, segundo = Mock(), Mock()
    deshabilitar_botones_dimension((primero, None, segundo))
    primero.disable.assert_called_once_with()
    segundo.disable.assert_called_once_with()


def test_matriz_cuadrada_carga_con_recorte_cache_compartido_y_una_notificacion():
    """La consolidación conserva dimensión máxima, texto e identidad del caché."""
    panel = PanelMatrizCuadrada()
    cache_original = panel.cache
    panel.cache[(100, 100)] = "anterior"
    panel.al_cambiar_datos = Mock()
    panel._renderizar_completa = Mock()
    datos = [[" 1/3 ", "0", "invalido"] + [" 0 "] * DIMENSION_MAXIMA_INVERSA
             for _ in range(DIMENSION_MAXIMA_INVERSA + 1)]
    panel.cargar_matriz(datos)
    assert panel.dimension == DIMENSION_MAXIMA_INVERSA
    assert panel.cache is cache_original
    assert panel.cache == {(fila, columna): valor
                           for fila in range(DIMENSION_MAXIMA_INVERSA)
                           for columna, valor in [(0, "1/3"), (2, "invalido")]}
    assert len(panel.obtener_datos_matriz()) == DIMENSION_MAXIMA_INVERSA
    panel.al_cambiar_datos.assert_called_once_with()
    panel._renderizar_completa.assert_called_once_with()
