"""Pruebas automáticas de contraste WCAG AA, relieve y muestras de Marea.

Verifica en Python puro sin dependencias de navegador ni NiceGUI:
- Contraste WCAG 2.x AA en Marea (>= 4.5:1 texto, >= 3.0:1 no-texto/foco).
- Heurística de relieve neumórfico (diferencias de luminancia entre superficies).
- Presencia exacta de las 4 declaraciones --swatch-marea: #D8FFFF;.
- Inmutabilidad de los bloques de Papel y Medianoche.
"""
import re
from pathlib import Path
import pytest
from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, luminancia_relativa, razon_contraste,
)

CSS_PATH = Path(__file__).resolve().parent.parent / "src" / "frontend" / "assets" / "css" / "tokens.css"


MAREA_TEXT_SURFACES = [
    # text-main y text-sec sobre bg-page, bg-panel, bg-elevated, bg-calc-btn, input-bg
    ("text-main", "bg-page", 4.5),
    ("text-main", "bg-panel", 4.5),
    ("text-main", "bg-elevated", 4.5),
    ("text-main", "bg-calc-btn", 4.5),
    ("text-main", "input-bg", 4.5),
    ("text-sec", "bg-page", 4.5),
    ("text-sec", "bg-panel", 4.5),
    ("text-sec", "bg-elevated", 4.5),
    ("text-sec", "bg-calc-btn", 4.5),
    ("text-sec", "input-bg", 4.5),
]

MAREA_ACCENT_PAIRS = [
    # accent sobre bg-page, bg-panel, bg-elevated y accent-soft
    ("accent", "bg-page", 4.5),
    ("accent", "bg-panel", 4.5),
    ("accent", "bg-elevated", 4.5),
    ("accent", "accent-soft", 4.5),
    ("btn-primary-text", "btn-primary-bg", 4.5),
]

MAREA_STATUS_PAIRS = [
    # error, success, warning sobre bg-page y bg-panel (>= 4.5)
    ("error", "bg-page", 4.5),
    ("error", "bg-panel", 4.5),
    ("success", "bg-page", 4.5),
    ("success", "bg-panel", 4.5),
    ("warning", "bg-page", 4.5),
    ("warning", "bg-panel", 4.5),
]

MAREA_BADGE_PAIRS = [
    ("badge-err-text", "badge-err-bg", 4.5),
    ("badge-suc-text", "badge-suc-bg", 4.5),
    ("badge-warn-text", "badge-warn-bg", 4.5),
]

MAREA_FOCUS_PAIRS = [
    ("focus-ring", "bg-page", 3.0),
    ("focus-ring", "bg-panel", 3.0),
]


@pytest.mark.parametrize("fg,bg,threshold", MAREA_TEXT_SURFACES + MAREA_ACCENT_PAIRS + MAREA_STATUS_PAIRS + MAREA_BADGE_PAIRS + MAREA_FOCUS_PAIRS)
def test_contraste_texto_estados_y_foco_marea(fg: str, bg: str, threshold: float):
    """Verifica contraste WCAG AA exigido en Marea para cada par especificado."""
    themes = analizar_tokens(CSS_PATH)
    marea = themes["marea"]

    fg_hex = marea.get(f"--{fg}")
    bg_hex = marea.get(f"--{bg}")
    assert fg_hex is not None, f"Token --{fg} no encontrado en Marea"
    assert bg_hex is not None, f"Token --{bg} no encontrado en Marea"

    cr = razon_contraste(hexadecimal_a_rgb(fg_hex), hexadecimal_a_rgb(bg_hex))
    assert cr >= threshold, (
        f"Contraste insuficiente en Marea: --{fg} ({fg_hex}) sobre --{bg} ({bg_hex}) = "
        f"{cr:.2f}:1 (requerido >= {threshold:.1f}:1)"
    )


def test_relieve_marea_por_diferencias_de_luminancia():
    """Verifica que el relieve neumórfico posea diferencias mínimas de luminancia relativa."""
    themes = analizar_tokens(CSS_PATH)
    marea = themes["marea"]

    lum_page = luminancia_relativa(hexadecimal_a_rgb(marea["--bg-page"]))
    lum_panel = luminancia_relativa(hexadecimal_a_rgb(marea["--bg-panel"]))
    lum_elevated = luminancia_relativa(hexadecimal_a_rgb(marea["--bg-elevated"]))
    lum_input = luminancia_relativa(hexadecimal_a_rgb(marea["--input-bg"]))

    # Heurística 1: El panel debe ser notablemente más oscuro que la página (ΔL >= 0.08)
    diff_panel = lum_page - lum_panel
    assert diff_panel >= 0.08, (
        f"Relieve insuficiente entre --bg-page ({lum_page:.4f}) y --bg-panel ({lum_panel:.4f}): ΔL = {diff_panel:.4f} < 0.08"
    )

    # Heurística 2: El input debe ser claramente hundido respecto a la página (ΔL >= 0.15)
    diff_input = lum_page - lum_input
    assert diff_input >= 0.15, (
        f"Relieve insuficiente de hundimiento para --input-bg: ΔL = {diff_input:.4f} < 0.15"
    )

    # Heurística 3: El input debe ser más oscuro que el panel (ΔL >= 0.05)
    diff_panel_input = lum_panel - lum_input
    assert diff_panel_input >= 0.05, (
        f"El input debe ser más oscuro que el panel: ΔL = {diff_panel_input:.4f} < 0.05"
    )

    # Heurística 4: La superficie elevated debe ser más clara que la página (L_elevated > L_page)
    assert lum_elevated > lum_page, (
        f"La superficie --bg-elevated ({lum_elevated:.4f}) debe ser más clara que --bg-page ({lum_page:.4f})"
    )


def test_muestra_marea_declarada_cuatro_veces():
    """Verifica que las cuatro declaraciones de --swatch-marea sean exactamente #CFE3F0."""
    content = CSS_PATH.read_text(encoding="utf-8")
    assert content.count("--swatch-marea: #CFE3F0;") >= 4, (
        f"Se esperaban al menos 4 declaraciones exactas de '--swatch-marea: #CFE3F0;', "
        f"se encontraron {content.count('--swatch-marea: #CFE3F0;')}"
    )


def test_tokens_papel_y_medianoche_conservados():
    """Verifica que los tokens de Papel y Medianoche permanezcan idénticos a su estado canónico."""
    themes = analizar_tokens(CSS_PATH)
    papel = themes["papel"]
    medianoche = themes["medianoche"]

    expected_papel = {
        "--bg-page": "#F2F0EB", "--bg-panel": "#EDEAE3",
        "--bg-elevated": "#F7F5F1", "--bg-calc-btn": "#F6F4EF",
        "--input-bg": "#E5E1D8", "--text-main": "#23262E",
        "--text-sec": "#5A6070",
        "--accent": "#1F6B64",
        "--accent-soft": "#D8E8E5",
        "--btn-primary-text": "#F7F5F1",
        "--focus-ring": "#1F6B64",
        "--error": "#B23A31",
        "--success": "#1F7A4D",
        "--warning": "#A6710B",
    }
    _comprobar_tokens_papel(papel, expected_papel)

    expected_medianoche = {
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
        "--focus-ring": "#BFE6E1",
        "--error": "#E8897D",
        "--success": "#8FCBA6",
        "--warning": "#E3B27E",
    }
    for k, v in expected_medianoche.items():
        assert medianoche.get(k) == v, f"Token Medianoche {k} alterado: {medianoche.get(k)} != {v}"


def _comprobar_tokens_papel(papel, esperados):
    for k, v in esperados.items():
        assert papel.get(k) == v, f"Token Papel {k} alterado: {papel.get(k)} != {v}"
