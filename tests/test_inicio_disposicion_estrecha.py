"""Contención y lectura del directorio de inicio en pantallas estrechas."""
from tests.comun_estilos import bloque_css, leer_css_inicio


def test_disposicion_estrecha_contiene_enlaces_y_encabezados():
    """Los encabezados y las secciones admiten el ancho disponible en un carril."""
    css = leer_css_inicio()
    estrecho = bloque_css(css, "@container (max-width: 40rem)")
    seccion = bloque_css(css, ".inicio-seccion {")
    assert ".inicio-presentacion" in estrecho
    assert ".inicio-secciones" in estrecho
    assert "grid-template-columns: minmax(0, 1fr)" in estrecho
    assert "min-width: 0" in seccion


def test_franja_y_enlaces_admiten_saltos_de_linea():
    """La franja puede pasar a otra línea y las etiquetas largas siguen visibles."""
    css = leer_css_inicio()
    franja = bloque_css(css, ".inicio-seccion-numeracion {")
    enlaces = bloque_css(css, ".inicio-enlace {")
    assert "flex-wrap: wrap" in franja
    assert "grid-column: 1 / -1" in franja
    assert "grid-template-columns: 2.5rem minmax(0, 1fr) auto" in enlaces
    assert "overflow-wrap: anywhere" in enlaces
    assert "min-height: 2.75rem" in enlaces
