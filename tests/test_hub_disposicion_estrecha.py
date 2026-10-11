"""Disposición de filas y encabezados del Hub en pantallas estrechas."""
from pathlib import Path

from tests.comun_estilos import buscar_cierre_bloque


THEME_CSS_PATH = Path("src/frontend/assets/css/vistas_hub_adaptable.css")


def bloque_hub_estrecho() -> str:
    """Lee las reglas que se aplican hasta 359 píxeles de ancho."""
    css = THEME_CSS_PATH.read_text(encoding="utf-8")
    start = css.index("@media (max-width: 359px) {")
    open_index = css.index("{", start)
    return css[start:buscar_cierre_bloque(css, open_index) + 1]


def test_disposicion_estrecha_contiene_tarjetas_y_encabezado():
    """Conserva las áreas de cuadrícula y el ancho mínimo de las tarjetas."""
    css = bloque_hub_estrecho()

    assert ".hub-pop-head" in css
    assert '"title close"' in css
    assert '"count count"' in css
    assert ".hub-pop-icon" in css
    assert "display: none" in css
    assert ".hub-tile" in css
    assert '"icon name"' in css
    assert '"icon desc"' in css
    assert '"mark mark"' in css
    assert ".hub-tile-mark" in css
    assert "min-width: 0" in css


def test_marca_de_fila_reserva_dos_lineas():
    """La selección destacada dispone de espacio sin desplazar la fila."""
    css = bloque_hub_estrecho()

    assert ".hub-row-mark" in css
    assert "min-height: 2.4em" in css
