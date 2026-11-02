"""Normalización matemática escapada para las descripciones visibles."""
import pytest

from src.frontend.componentes.reproductor_pasos.textos import formatear_descripcion_html


@pytest.mark.parametrize("texto,esperado", [
    ("Sin LaTeX", "Sin LaTeX"),
    ("", ""),
    ('<script>alert("x")</script>', '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;'),
    ("a < b & c", "a &lt; b &amp; c"),
    (r"A_{i_{j}}^{n^{2}}", "A<sub>i<sub>j</sub></sub><sup>n<sup>2</sup></sup>"),
    (r"A^T\cdot A_{1}", "Aᵀ· A<sub>1</sub>"),
    ("AA^{-1}=I", "A·A<sup>-1</sup>=I"),
    ("A^{-1}A=I", "A<sup>-1</sup>·A=I"),
    ('A^{<img src=x onerror="alert(1)">}', 'A<sup>&lt;img src=x onerror=&quot;alert(1)&quot;&gt;</sup>'),
    ("A^{sin cerrar", "A^{sin cerrar"),
])
def test_formatear_descripcion_html(texto, esperado):
    """Conserva texto, resuelve índices anidados y evita interpretar entradas como HTML."""
    assert formatear_descripcion_html(texto) == esperado
