"""Pruebas automáticas de contraste WCAG para los tres temas."""
from pathlib import Path
import pytest
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste

RUTA_CSS = Path(__file__).resolve().parent.parent / "src" / "frontend" / "recursos" / "css" / "tokens.css"


TEMAS = ["papel", "marea", "medianoche"]

# Los umbrales distinguen texto normal e indicadores sin texto.
REQUISITOS_CONTRASTE = [
    # texto-principal sobre bg-page, bg-panel, fondo-elevado e input-bg (>= 4.5:1)
    ("text-main", "bg-page", 4.5),
    ("text-main", "bg-panel", 4.5),
    ("text-main", "bg-elevated", 4.5),
    ("text-main", "input-bg", 4.5),
    # texto-secundario sobre bg-page, bg-panel, fondo-elevado e input-bg (>= 4.5:1)
    ("text-sec", "bg-page", 4.5),
    ("text-sec", "bg-panel", 4.5),
    ("text-sec", "bg-elevated", 4.5),
    ("text-sec", "input-bg", 4.5),
    # accent sobre bg-page, bg-panel y fondo-elevado (>= 4.5:1)
    ("accent", "bg-page", 4.5),
    ("accent", "bg-panel", 4.5),
    ("accent", "bg-elevated", 4.5),
    # accent sobre accent-soft (>= 4.5:1)
    ("accent", "accent-soft", 4.5),
    # btn-primary-text sobre btn-primary-bg (>= 4.5:1)
    ("btn-primary-text", "btn-primary-bg", 4.5),
    # error sobre bg-panel (>= 4.5:1 para texto de error)
    ("error", "bg-panel", 4.5),
    # badge-warn-text sobre bg-panel (>= 4.5:1 para texto en .texto-advertencia)
    ("badge-warn-text", "bg-panel", 4.5),
    # cada par badge (texto/fondo) (>= 4.5:1)
    ("badge-err-text", "badge-err-bg", 4.5),
    ("badge-suc-text", "badge-suc-bg", 4.5),
    ("badge-warn-text", "badge-warn-bg", 4.5),
    # focus-ring vs bg-page (>= 3.0:1 no-texto)
    ("focus-ring", "bg-page", 3.0),
]


@pytest.mark.parametrize('nombre_tema', TEMAS)
@pytest.mark.parametrize('frente,fondo,umbral', REQUISITOS_CONTRASTE)
def test_contraste_texto_en_superficies(nombre_tema: str, frente: str, fondo: str, umbral: float):
    """Verifica que cada par especificado cumpla con el ratio de contraste WCAG AA exigido."""
    temas = analizar_tokens(RUTA_CSS)
    t = temas[nombre_tema]

    hexadecimal_frente = t.get(f"--{frente}")
    hexadecimal_fondo = t.get(f"--{fondo}")

    assert hexadecimal_frente is not None, f"Token --{frente} no encontrado en tema {nombre_tema}"
    assert hexadecimal_fondo is not None, f"Token --{fondo} no encontrado en tema {nombre_tema}"
    assert hexadecimal_frente.startswith("#"), f"Token --{frente} en {nombre_tema} no es un color hex: {hexadecimal_frente}"
    assert hexadecimal_fondo.startswith("#"), f"Token --{fondo} en {nombre_tema} no es un color hex: {hexadecimal_fondo}"

    rgb_frente = hexadecimal_a_rgb(hexadecimal_frente)
    rgb_fondo = hexadecimal_a_rgb(hexadecimal_fondo)
    proporcion = razon_contraste(rgb_frente, rgb_fondo)

    assert proporcion >= umbral, (
        f"Contraste insuficiente en {nombre_tema}: --{frente} ({hexadecimal_frente}) sobre --{fondo} ({hexadecimal_fondo}) = "
        f"{proporcion:.2f}:1 (requerido >= {umbral:.1f}:1)"
    )
