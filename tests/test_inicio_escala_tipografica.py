"""Escala tipográfica y ancho de la matriz del inicio."""
from decimal import Decimal
from pathlib import Path
import re
from tests.comun_estilos import leer_css_inicio


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/theme.css")
RUTA_VISTA_INICIO = Path("src/frontend/vistas/inicio/vista_inicio.py")


def cuerpo_regla(css: str, selector: str) -> str:
    """Localiza una regla simple por su selector completo."""
    coincidencia = re.search(
        rf"(?m)^{re.escape(selector)}\s*\{{([^{{}}]*)\}}",
        css,
    )
    assert coincidencia is not None, f"No se encontró la regla {selector}"
    return coincidencia.group(1)


def minimo_tipografico_rem(css: str, selector: str) -> Decimal:
    """Extrae el tamaño mínimo en rem de una declaración clamp."""
    cuerpo = cuerpo_regla(css, selector)
    coincidencia = re.search(r"font-size:\s*clamp\(\s*([\d.]+)rem\s*,", cuerpo)
    assert coincidencia is not None, f"{selector} no declara un font-size clamp en rem"
    return Decimal(coincidencia.group(1))


def test_escala_inicio_y_propiedades_permitidas():
    """La matriz conserva ancho limitado y tamaños tipográficos mínimos."""
    from tests.comun import leer_css_completo
    vista = RUTA_VISTA_INICIO.read_text(encoding="utf-8")
    css_completo = leer_css_completo()
    css = leer_css_inicio()

    assert "hub-theme" not in vista
    assert "renderizar_boton_tema" not in vista
    assert ".hub-theme" not in css_completo
    assert "width: min(100%, 72rem)" in cuerpo_regla(css, ".inicio-matriz")

    assert minimo_tipografico_rem(css, ".inicio-titulo") >= Decimal("2.5")
    assert minimo_tipografico_rem(css, ".inicio-titulo-fila") >= Decimal("1.4")
    assert minimo_tipografico_rem(css, ".inicio-descripcion-fila") >= Decimal("0.9375")

    assert "100vh" not in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", css)
