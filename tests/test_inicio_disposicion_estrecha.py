"""Disposición de filas y encabezados del inicio en pantallas estrechas."""
from pathlib import Path

from tests.comun_estilos import buscar_cierre_bloque


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/vistas_inicio_adaptable.css")


def bloque_inicio_estrecho() -> str:
    """Lee las reglas que se aplican hasta 359 píxeles de ancho."""
    css = RUTA_CSS_TEMAS.read_text(encoding="utf-8")
    inicio = css.index("@media (max-width: 359px) {")
    indice_apertura = css.index("{", inicio)
    return css[inicio:buscar_cierre_bloque(css, indice_apertura) + 1]


def test_disposicion_estrecha_contiene_tarjetas_y_encabezado():
    """Conserva las áreas de cuadrícula y el ancho mínimo de las tarjetas."""
    css = bloque_inicio_estrecho()

    assert ".inicio-dialogo-cabecera" in css
    assert '"titulo cerrar"' in css
    assert '"conteo conteo"' in css
    assert ".inicio-dialogo-icono" in css
    assert "display: none" in css
    assert ".inicio-tarjeta" in css
    assert '"icono nombre"' in css
    assert '"icono descripcion"' in css
    assert '"marca marca"' in css
    assert ".inicio-tarjeta-marca" in css
    assert "min-width: 0" in css


def test_marca_de_fila_reserva_dos_lineas():
    """La selección destacada dispone de espacio sin desplazar la fila."""
    css = bloque_inicio_estrecho()

    assert ".inicio-marca-fila" in css
    assert "min-height: 2.4em" in css
