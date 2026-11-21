"""Escala tipográfica y ancho del directorio de inicio."""
from decimal import Decimal
from pathlib import Path
import re
from tests.comun_estilos import leer_css_inicio


RUTA_CSS_TEMAS = Path("src/frontend/recursos/css/base/tokens.css")
RUTA_VISTA_INICIO = Path("src/frontend/vistas/inicio/vista_inicio.py")


def cuerpo_regla(css: str, selector: str) -> str:
    """Localiza una regla simple por su selector completo."""
    coincidencias = re.findall(
        rf"(?m)^{re.escape(selector)}\s*\{{([^{{}}]*)\}}",
        css,
    )
    assert coincidencias, f"No se encontró la regla {selector}"
    return "\n".join(coincidencias)


def minimo_tipografico_rem(css: str, selector: str) -> Decimal:
    """Extrae el mínimo de la escala y resuelve un token tipográfico cuando se usa."""
    cuerpo = cuerpo_regla(css, selector)
    coincidencia = re.search(r"font-size:\s*clamp\(\s*(?:([\d.]+)rem|var\((--[\w-]+)\))\s*,", cuerpo)
    assert coincidencia is not None, f"{selector} no declara un mínimo tipográfico en rem"
    minimo, token = coincidencia.groups()
    if token:
        temas = RUTA_CSS_TEMAS.read_text(encoding="utf-8")
        definido = re.search(rf"{re.escape(token)}:\s*([\d.]+)rem\b", temas)
        assert definido is not None, f"El mínimo {token} debe estar expresado en rem"
        minimo = definido.group(1)
    return Decimal(minimo)


def test_escala_inicio_y_propiedades_permitidas():
    """La portada contiene el directorio y aplica mínimos tipográficos legibles."""
    from tests.comun import leer_css_completo
    vista = RUTA_VISTA_INICIO.read_text(encoding="utf-8")
    css_completo = leer_css_completo()
    css = leer_css_inicio()

    assert "hub-theme" not in vista
    assert "renderizar_boton_tema" in vista
    assert ".hub-theme" not in css_completo
    assert "width: 100%" in cuerpo_regla(css, ".inicio-raiz")
    assert "max-width: 71rem" in cuerpo_regla(css, ".inicio-raiz")

    assert minimo_tipografico_rem(css, ".inicio-titulo") >= Decimal("2.25")
    assert minimo_tipografico_rem(css, ".inicio-seccion-titulo") >= Decimal("1.35")
    assert minimo_tipografico_rem(css, ".inicio-descripcion") >= Decimal("0.9375")

    assert "100vh" not in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not re.search(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", css)
