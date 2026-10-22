"""Tokens, sombras y contraste del tema Marea."""
from pathlib import Path
import pytest
from tests.comun_estilos import analizar_tokens, hexadecimal_a_rgb, razon_contraste

RUTA_CSS = Path("src/frontend/recursos/css/tokens.css")

HEXADECIMALES_MAREA_ESPERADOS = {
    "--bg-page": "#CFE3F0",
    "--bg-panel": "#BDD5E6",
    "--bg-elevated": "#E4F0F8",
    "--bg-calc-btn": "#D6E7F3",
    "--input-bg": "#A9C6DB",
    "--accent-soft": "#C2DEE8",
    "--btn-primary-text": "#E4F0F8",
}

SOMBRAS_MAREA_ESPERADAS = {
    "--shadow-dark": "rgba(28, 66, 96, 0.22)",
    "--shadow-light": "rgba(255, 255, 255, 0.95)",
}

PAPEL_ESPERADO = {
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

MEDIANOCHE_ESPERADA = {
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

PARES_CONTRASTE_MAREA = [
    # texto-principal y texto-secundario sobre bg-page, bg-panel, fondo-elevado, input-bg
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
    temas = analizar_tokens(RUTA_CSS, pasadas=1, exigir_cierre=False)
    marea = temas["marea"]

    for token, esperado in HEXADECIMALES_MAREA_ESPERADOS.items():
        actual = marea.get(token)
        assert actual == esperado, (
            f"Token {token} en Marea tiene valor {actual}, se esperaba {esperado}"
        )

    for token, esperado in SOMBRAS_MAREA_ESPERADAS.items():
        actual = marea.get(token)
        assert actual == esperado, (
            f"Sombra {token} en Marea tiene valor {actual}, se esperaba {esperado}"
        )


def test_tokens_papel_y_medianoche_conservados():
    """Verifica que los tokens de Papel y Medianoche no hayan cambiado."""
    temas = analizar_tokens(RUTA_CSS, pasadas=1, exigir_cierre=False)
    papel = temas["papel"]
    medianoche = temas["medianoche"]

    for token, esperado in PAPEL_ESPERADO.items():
        actual = papel.get(token)
        assert actual == esperado, (
            f"Token {token} en Papel cambio a {actual}, se esperaba conservar {esperado}"
        )

    for token, esperado in MEDIANOCHE_ESPERADA.items():
        actual = medianoche.get(token)
        assert actual == esperado, (
            f"Token {token} en Medianoche cambio a {actual}, se esperaba conservar {esperado}"
        )


@pytest.mark.parametrize('token_frente,token_fondo', PARES_CONTRASTE_MAREA)
def test_contraste_marea(token_frente: str, token_fondo: str):
    """Verifica contraste WCAG >= 4.5 en Marea para cada par especificado."""
    temas = analizar_tokens(RUTA_CSS, pasadas=1, exigir_cierre=False)
    marea = temas["marea"]

    hexadecimal_frente = marea.get(f"--{token_frente}")
    hexadecimal_fondo = marea.get(f"--{token_fondo}")

    assert hexadecimal_frente is not None, f"Token --{token_frente} no encontrado en Marea"
    assert hexadecimal_fondo is not None, f"Token --{token_fondo} no encontrado en Marea"

    rgb_frente = hexadecimal_a_rgb(hexadecimal_frente, limpiar_espacios=False)
    rgb_fondo = hexadecimal_a_rgb(hexadecimal_fondo, limpiar_espacios=False)
    proporcion = razon_contraste(rgb_frente, rgb_fondo)

    assert proporcion >= 4.5, (
        f"Contraste insuficiente en Marea: {token_frente} ({hexadecimal_frente}) sobre {token_fondo} ({hexadecimal_fondo}) = "
        f"{proporcion:.2f}:1 (requerido >= 4.5:1)"
    )
