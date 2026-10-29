"""Comprueba los tiempos compartidos de los estados interactivos."""
from pathlib import Path

from tests.comun_estilos import bloque_css


RAIZ_CSS = Path("src/frontend/recursos/css")


def leer_estilos(nombre):
    """Devuelve el contenido UTF-8 de una hoja de estilos del cliente."""
    return (RAIZ_CSS / nombre).read_text(encoding="utf-8")


def test_pulsacion_y_regreso_comparten_tokens():
    """Los controles usan tiempos distintos al presionar y al soltar."""
    controles = leer_estilos("componentes_controles.css")
    for selector in (".boton-principal", ".boton-discreto", ".boton-icono",
                     ".calculadora-boton", ".marca-enlace-logotipo"):
        assert "var(--dur-release)" in bloque_css(controles, selector + " {")
        assert "var(--dur-press)" in bloque_css(controles, selector + ":active {")


def test_selector_geometria_y_regreso_inicio():
    """El selector, el deslizador y las filas responden con los tokens previstos."""
    selector = leer_estilos("selector_opciones.css")
    geometria = leer_estilos("vistas_geometria.css")
    inicio = leer_estilos("vistas_inicio_matriz.css")
    assert "var(--dur-state)" in bloque_css(selector, ".selector-opciones-cambiando .selector-opciones-indicador")
    assert "var(--dur-press)" in bloque_css(selector, ".selector-opciones-opcion:active")
    assert "var(--dur-release)" in bloque_css(geometria, ".geometria-deslizador-entrada")
    assert "var(--dur-press)" in bloque_css(geometria, ".geometria-deslizador-entrada:active")
    fila = bloque_css(inicio, ".inicio-fila[data-interaccion]")
    assert "var(--dur-release)" in fila
    assert "var(--dur-press)" in bloque_css(inicio, ".inicio-fila:active")
