"""Regla de partición de palabras de los bloques textuales de Glosa."""
from tests.comun import leer_css_completo
from tests.comun_estilos import bloque_css


def test_bloque_textual_glosa_admite_palabras_sin_espacios():
    """La clase usada por el texto mantiene la partición aunque cambie su hoja CSS."""
    css = leer_css_completo()
    assert "overflow-wrap: anywhere;" in bloque_css(css, ".glosa-texto-bloque")
