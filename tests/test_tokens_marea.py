"""Tokens, sombras y contraste del tema Marea."""
from pathlib import Path
import pytest
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste

CSS_PATH = Path("src/frontend/assets/css/tokens.css")

EXPECTED_MAREA_HEX = {
    "--bg-page": "#CFE3F0",
    "--bg-panel": "#BDD5E6",
    "--bg-elevated": "#E4F0F8",
    "--bg-calc-btn": "#D6E7F3",
    "--input-bg": "#A9C6DB",
    "--accent-soft": "#C2DEE8",
    "--btn-primary-text": "#E4F0F8",
}

EXPECTED_MAREA_SHADOWS = {
    "--shadow-dark": "rgba(28, 66, 96, 0.22)",
    "--shadow-light": "rgba(255, 255, 255, 0.95)",
}

EXPECTED_PAPEL = {
    "--bg-page": "#F2F0EB",
    "--bg-panel": "#EDEAE3",
    "--bg-elevated": "#F7F5F1",
    "--bg-calc-btn": "#F6F4EF",
    "--input-bg": "#E5E1D8",
    "--text-main": "#23262E",
    "--text-sec": "#5A6070",
    "--accent": "#1F6B64",
    "--accent-soft": "#D8E8E5",
    "--btn-primary-text": "#F7F5F1",
}

EXPECTED_MEDIANOCHE = {
    "--bg-page": "#082338",
    "--bg-panel": "#0A2B45",
    "--bg-elevated": "#0D3554",
    "--bg-calc-btn": "#0D3554",
    "--input-bg": "#061D2E",
    "--text-main": "#EAF6FF",
    "--text-sec": "#B1D4F0",
    "--accent": "#BFE6E1",
    "--accent-soft": "#14403C",
    "--btn-primary-text": "#082338",
}

MAREA_CONTRAST_PAIRS = [
    # text-main y text-sec sobre bg-page, bg-panel, bg-elevated, input-bg
    ("text-main", "bg-page"),
    ("text-main", "bg-panel"),
    ("text-main", "bg-elevated"),
    ("text-main", "input-bg"),
    ("text-sec", "bg-page"),
    ("text-sec", "bg-panel"),
    ("text-sec", "bg-elevated"),
    ("text-sec", "input-bg"),
    # accent sobre bg-page, bg-panel, input-bg y accent-soft
    ("accent", "bg-page"),
    ("accent", "bg-panel"),
    ("accent", "input-bg"),
    ("accent", "accent-soft"),
    # btn-primary-text sobre accent
    ("btn-primary-text", "accent"),
]


def test_colores_y_sombras_marea():
    """Verifica que los tokens de Marea tengan exactamente los valores especificados."""
    themes = analizar_tokens(CSS_PATH, pasadas=1, exigir_cierre=False)
    marea = themes["marea"]

    for token, expected in EXPECTED_MAREA_HEX.items():
        actual = marea.get(token)
        assert actual == expected, (
            f"Token {token} en Marea tiene valor {actual}, se esperaba {expected}"
        )

    for token, expected in EXPECTED_MAREA_SHADOWS.items():
        actual = marea.get(token)
        assert actual == expected, (
            f"Sombra {token} en Marea tiene valor {actual}, se esperaba {expected}"
        )


def test_tokens_papel_y_medianoche_conservados():
    """Verifica que los tokens de Papel y Medianoche no hayan cambiado."""
    themes = analizar_tokens(CSS_PATH, pasadas=1, exigir_cierre=False)
    papel = themes["papel"]
    medianoche = themes["medianoche"]

    for token, expected in EXPECTED_PAPEL.items():
        actual = papel.get(token)
        assert actual == expected, (
            f"Token {token} en Papel cambio a {actual}, se esperaba conservar {expected}"
        )

    for token, expected in EXPECTED_MEDIANOCHE.items():
        actual = medianoche.get(token)
        assert actual == expected, (
            f"Token {token} en Medianoche cambio a {actual}, se esperaba conservar {expected}"
        )


@pytest.mark.parametrize("fg_token,bg_token", MAREA_CONTRAST_PAIRS)
def test_contraste_marea(fg_token: str, bg_token: str):
    """Verifica contraste WCAG >= 4.5 en Marea para cada par especificado."""
    themes = analizar_tokens(CSS_PATH, pasadas=1, exigir_cierre=False)
    marea = themes["marea"]

    fg_hex = marea.get(f"--{fg_token}")
    bg_hex = marea.get(f"--{bg_token}")

    assert fg_hex is not None, f"Token --{fg_token} no encontrado en Marea"
    assert bg_hex is not None, f"Token --{bg_token} no encontrado en Marea"

    rgb_fg = hexadecimal_a_rgb(fg_hex, limpiar_espacios=False)
    rgb_bg = hexadecimal_a_rgb(bg_hex, limpiar_espacios=False)
    ratio = razon_contraste(rgb_fg, rgb_bg)

    assert ratio >= 4.5, (
        f"Contraste insuficiente en Marea: {fg_token} ({fg_hex}) sobre {bg_token} ({bg_hex}) = "
        f"{ratio:.2f}:1 (requerido >= 4.5:1)"
    )
