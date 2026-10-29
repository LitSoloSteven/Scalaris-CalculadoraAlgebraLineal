"""Comprueba la configuración de movimiento de paneles y componentes Quasar."""
from nicegui import ui
from pathlib import Path

from src.frontend.aplicacion import configurar_movimiento_componentes
from tests.comun_estilos import bloque_css


def leer_estilos(nombre):
    """Lee una hoja de estilos del cliente en UTF-8."""
    return (Path("src/frontend/recursos/css") / nombre).read_text(encoding="utf-8")


def test_componentes_quasar_leen_sus_tokens(monkeypatch):
    """Las propiedades dinámicas conservan una sola fuente de duraciones."""
    recibidas = {}
    componentes = (ui.dialog, ui.tab_panels, ui.expansion, ui.menu, ui.tooltip)
    for componente in componentes:
        monkeypatch.setattr(componente, "default_props", lambda valor, clase=componente: recibidas.update({clase: valor}))
    configurar_movimiento_componentes()
    for componente, token in zip(componentes, ("--dur-view", "--dur-state", "--dur-panel", "--dur-panel", "--dur-state")):
        assert "window.scalaris.movimiento.duracion" in recibidas[componente]
        assert token in recibidas[componente]


def test_dialogo_inicio_y_aviso_utilizan_tokens():
    """Los diálogos y avisos distinguen entrada y salida."""
    inicio = leer_estilos("vistas_inicio_ventanas_emergentes.css")
    base = leer_estilos("base.css")
    assert "var(--dur-view-exit)" in bloque_css(inicio, ".inicio-dialogo-tarjeta {")
    assert "var(--dur-view)" in bloque_css(inicio, ".inicio-dialogo[open][data-abierto] .inicio-dialogo-tarjeta {")
    assert "var(--dur-panel)" in bloque_css(base, ".q-notification {")
    assert "var(--dur-panel-exit)" in bloque_css(base, '.q-notification[class*="-leave-active"]')
