"""Contraste WCAG de texto, estados y foco en los tres temas."""
import pytest
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste

CSS_PATH = 'src/frontend/assets/css/tokens.css'

PAIRS = [
    ('text-main', 'bg-page', 4.5),
    ('text-main', 'bg-panel', 4.5),
    ('text-main', 'bg-elevated', 4.5),
    ('text-main', 'input-bg', 4.5),
    ('text-sec', 'bg-page', 4.5),
    ('text-sec', 'bg-panel', 4.5),
    ('text-sec', 'bg-elevated', 4.5),
    ('text-sec', 'input-bg', 4.5),
    ('text-placeholder', 'input-bg', 4.5),
    ('accent', 'bg-page', 4.5),
    ('accent', 'bg-panel', 4.5),
    ('accent', 'bg-elevated', 4.5),
    ('accent', 'accent-soft', 4.5),
    ('btn-primary-text', 'btn-primary-bg', 4.5),
    ('badge-err-text', 'badge-err-bg', 4.5),
    ('badge-suc-text', 'badge-suc-bg', 4.5),
    ('badge-warn-text', 'badge-warn-bg', 4.5),
    ('error', 'bg-panel', 3.0),
    ('success', 'bg-panel', 3.0),
    ('warning', 'bg-panel', 3.0),
    ('focus-ring', 'bg-page', 3.0),
]

THEMES = ['papel', 'marea', 'medianoche']

@pytest.mark.parametrize("theme_name", THEMES)
@pytest.mark.parametrize("fg,bg,threshold", PAIRS)
def test_contraste_texto_estados_y_foco(theme_name, fg, bg, threshold):
    """Cada par conserva su umbral WCAG en cada tema."""
    themes = analizar_tokens(CSS_PATH, pasadas=1, exigir_cierre=False)
    t = themes[theme_name]
    fg_hex = t.get(f'--{fg}')
    bg_hex = t.get(f'--{bg}')
    assert fg_hex, f"Token --{fg} no encontrado en tema {theme_name}"
    assert bg_hex, f"Token --{bg} no encontrado en tema {theme_name}"

    rgb_fg = hexadecimal_a_rgb(fg_hex, limpiar_espacios=False)
    rgb_bg = hexadecimal_a_rgb(bg_hex, limpiar_espacios=False)
    cr = razon_contraste(rgb_fg, rgb_bg)
    assert cr >= threshold, (
        f"Contraste insuficiente en {theme_name}: {fg} ({fg_hex}) sobre {bg} ({bg_hex}) = "
        f"{cr:.2f}:1 (requerido >= {threshold}:1)"
    )
