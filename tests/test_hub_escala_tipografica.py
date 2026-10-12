"""Escala tipográfica y ancho de la matriz del Hub."""
from decimal import Decimal
from pathlib import Path
import re
from tests.comun_estilos import leer_css_hub


THEME_CSS_PATH = Path("src/frontend/assets/css/theme.css")
VIEW_HUB_PATH = Path("src/frontend/vistas/hub/view_hub.py")


def cuerpo_regla(css: str, selector: str) -> str:
    """Localiza una regla simple por su selector completo."""
    match = re.search(
        rf"(?m)^{re.escape(selector)}\s*\{{([^{{}}]*)\}}",
        css,
    )
    assert match is not None, f"No se encontró la regla {selector}"
    return match.group(1)


def minimo_tipografico_rem(css: str, selector: str) -> Decimal:
    """Extrae el tamaño mínimo en rem de una declaración clamp."""
    body = cuerpo_regla(css, selector)
    match = re.search(r"font-size:\s*clamp\(\s*([\d.]+)rem\s*,", body)
    assert match is not None, f"{selector} no declara un font-size clamp en rem"
    return Decimal(match.group(1))


def test_escala_hub_y_propiedades_permitidas():
    """La matriz conserva ancho limitado y tamaños tipográficos mínimos."""
    from tests.comun import leer_css_completo
    view = VIEW_HUB_PATH.read_text(encoding="utf-8")
    full_css = leer_css_completo()
    css = leer_css_hub()

    assert "hub-theme" not in view
    assert "renderizar_boton_tema" not in view
    assert ".hub-theme" not in full_css
    assert "width: min(100%, 72rem)" in cuerpo_regla(css, ".hub-matrix")

    assert minimo_tipografico_rem(css, ".hub-title") >= Decimal("2.5")
    assert minimo_tipografico_rem(css, ".hub-row-title") >= Decimal("1.4")
    assert minimo_tipografico_rem(css, ".hub-row-blurb") >= Decimal("0.9375")

    assert "100vh" not in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", css)
