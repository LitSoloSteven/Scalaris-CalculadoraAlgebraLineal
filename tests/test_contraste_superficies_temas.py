"""Pruebas automáticas de contraste WCAG para los tres temas.

Verifica cumplimiento de contraste WCAG AA:
- Texto normal: ratio >= 4.5:1
- Elementos gráficos / indicadores / no-texto: ratio >= 3.0:1
"""
from pathlib import Path
import pytest
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste

CSS_PATH = Path(__file__).resolve().parent.parent / "src" / "frontend" / "assets" / "css" / "tokens.css"


THEMES = ["papel", "marea", "medianoche"]

# Los umbrales distinguen texto normal e indicadores sin texto.
CONTRAST_REQUIREMENTS = [
    # text-main sobre bg-page, bg-panel, bg-elevated e input-bg (>= 4.5:1)
    ("text-main", "bg-page", 4.5),
    ("text-main", "bg-panel", 4.5),
    ("text-main", "bg-elevated", 4.5),
    ("text-main", "input-bg", 4.5),
    # text-sec sobre bg-page, bg-panel, bg-elevated e input-bg (>= 4.5:1)
    ("text-sec", "bg-page", 4.5),
    ("text-sec", "bg-panel", 4.5),
    ("text-sec", "bg-elevated", 4.5),
    ("text-sec", "input-bg", 4.5),
    # accent sobre bg-page, bg-panel y bg-elevated (>= 4.5:1)
    ("accent", "bg-page", 4.5),
    ("accent", "bg-panel", 4.5),
    ("accent", "bg-elevated", 4.5),
    # accent sobre accent-soft (>= 4.5:1)
    ("accent", "accent-soft", 4.5),
    # btn-primary-text sobre btn-primary-bg (>= 4.5:1)
    ("btn-primary-text", "btn-primary-bg", 4.5),
    # error sobre bg-panel (>= 4.5:1 para texto de error en .text-err)
    ("error", "bg-panel", 4.5),
    # badge-warn-text sobre bg-panel (>= 4.5:1 para texto en .text-warn)
    ("badge-warn-text", "bg-panel", 4.5),
    # cada par badge (texto/fondo) (>= 4.5:1)
    ("badge-err-text", "badge-err-bg", 4.5),
    ("badge-suc-text", "badge-suc-bg", 4.5),
    ("badge-warn-text", "badge-warn-bg", 4.5),
    # focus-ring vs bg-page (>= 3.0:1 no-texto)
    ("focus-ring", "bg-page", 3.0),
]


@pytest.mark.parametrize("theme_name", THEMES)
@pytest.mark.parametrize("fg,bg,threshold", CONTRAST_REQUIREMENTS)
def test_contraste_texto_en_superficies(theme_name: str, fg: str, bg: str, threshold: float):
    """Verifica que cada par especificado cumpla con el ratio de contraste WCAG AA exigido."""
    themes = analizar_tokens(CSS_PATH)
    t = themes[theme_name]

    fg_hex = t.get(f"--{fg}")
    bg_hex = t.get(f"--{bg}")

    assert fg_hex is not None, f"Token --{fg} no encontrado en tema {theme_name}"
    assert bg_hex is not None, f"Token --{bg} no encontrado en tema {theme_name}"
    assert fg_hex.startswith("#"), f"Token --{fg} en {theme_name} no es un color hex: {fg_hex}"
    assert bg_hex.startswith("#"), f"Token --{bg} en {theme_name} no es un color hex: {bg_hex}"

    rgb_fg = hexadecimal_a_rgb(fg_hex)
    rgb_bg = hexadecimal_a_rgb(bg_hex)
    ratio = razon_contraste(rgb_fg, rgb_bg)

    assert ratio >= threshold, (
        f"Contraste insuficiente en {theme_name}: --{fg} ({fg_hex}) sobre --{bg} ({bg_hex}) = "
        f"{ratio:.2f}:1 (requerido >= {threshold:.1f}:1)"
    )
