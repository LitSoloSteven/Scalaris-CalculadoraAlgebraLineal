"""Regresiones de los lectores CSS compartidos y sus variantes históricas."""
import pytest

from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, luminancia_relativa,
    razon_contraste, bloque_css, buscar_cierre_bloque,
)


def test_tokens_resuelven_referencias_segun_numero_de_pasadas(tmp_path):
    """La extracción preserva resolución simple e iterativa de referencias."""
    ruta = tmp_path / "tokens.css"
    ruta.write_text(":root {--a: var(--b); --b: var(--c); --c: #ffffff;}", encoding="utf-8")
    assert analizar_tokens(ruta, pasadas=1)["papel"]["--a"] == "var(--c)"
    assert analizar_tokens(ruta)["papel"]["--a"] == "#ffffff"


def test_tokens_respetan_temas_y_comentarios(tmp_path):
    """La raíz inicia Papel y las declaraciones temáticas actualizan sus tokens."""
    ruta = tmp_path / "tokens.css"
    ruta.write_text(
        ':root {--a: #000000; color: red;} :root[data-theme="papel"] {--a: #111111;}'
        ':root[data-theme="marea"] {--a: #222222 /* motivo */;}'
        ':root[data-theme="medianoche"] {--a: #333333;}', encoding="utf-8",
    )
    assert analizar_tokens(ruta) == {
        "papel": {"--a": "#111111"}, "marea": {"--a": "#222222"},
        "medianoche": {"--a": "#333333"},
    }


def test_contraste_extremos_y_simetria():
    """Blanco y negro producen el contraste máximo y el orden no lo altera."""
    blanco = hexadecimal_a_rgb("#ffffff")
    negro = hexadecimal_a_rgb("#000000")
    assert luminancia_relativa(negro) == 0
    assert luminancia_relativa(blanco) == 1
    assert razon_contraste(blanco, negro) == 21
    assert razon_contraste(negro, blanco) == 21
    assert razon_contraste(blanco, blanco) == 1


def test_bloques_anidados_y_bloque_sin_cierre():
    """La búsqueda respeta llaves anidadas y rechaza un bloque incompleto."""
    assert bloque_css("@media { .a { opacity: 0; } }", "@media") == " .a { opacity: 0; } "
    with pytest.raises(AssertionError, match="Bloque CSS sin cerrar"):
        buscar_cierre_bloque(".a {", 3)
