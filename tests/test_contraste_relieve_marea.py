"""Pruebas automáticas de contraste WCAG AA, relieve y muestras de Marea."""
import re
from pathlib import Path
import pytest
from tests.comun_estilos import (
    analizar_tokens, hexadecimal_a_rgb, luminancia_relativa, razon_contraste,
)

RUTA_CSS = Path(__file__).resolve().parent.parent / "src" / "frontend" / "recursos" / "css" / "tokens.css"


SUPERFICIES_TEXTO_MAREA = [
    # texto-principal y texto-secundario sobre bg-page, bg-panel, fondo-elevado, bg-calc-btn, input-bg
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

PARES_ACENTO_MAREA = [
    # accent sobre bg-page, bg-panel, fondo-elevado y accent-soft
    ("accent", "bg-page", 4.5),
    ("accent", "bg-panel", 4.5),
    ("accent", "bg-elevated", 4.5),
    ("accent", "accent-soft", 4.5),
    ("btn-primary-text", "btn-primary-bg", 4.5),
]

PARES_ESTADO_MAREA = [
    # error, success, warning sobre bg-page y bg-panel (>= 4.5)
    ("error", "bg-page", 4.5),
    ("error", "bg-panel", 4.5),
    ("success", "bg-page", 4.5),
    ("success", "bg-panel", 4.5),
    ("warning", "bg-page", 4.5),
    ("warning", "bg-panel", 4.5),
]

PARES_INDICADOR_MAREA = [
    ("badge-err-text", "badge-err-bg", 4.5),
    ("badge-suc-text", "badge-suc-bg", 4.5),
    ("badge-warn-text", "badge-warn-bg", 4.5),
]

PARES_FOCO_MAREA = [
    ("focus-ring", "bg-page", 3.0),
    ("focus-ring", "bg-panel", 3.0),
]


@pytest.mark.parametrize('frente,fondo,umbral', SUPERFICIES_TEXTO_MAREA + PARES_ACENTO_MAREA + PARES_ESTADO_MAREA + PARES_INDICADOR_MAREA + PARES_FOCO_MAREA)
def test_contraste_texto_estados_y_foco_marea(frente: str, fondo: str, umbral: float):
    """Verifica contraste WCAG AA exigido en Marea para cada par especificado."""
    temas = analizar_tokens(RUTA_CSS)
    marea = temas["marea"]

    hexadecimal_frente = marea.get(f"--{frente}")
    hexadecimal_fondo = marea.get(f"--{fondo}")
    assert hexadecimal_frente is not None, f"Token --{frente} no encontrado en Marea"
    assert hexadecimal_fondo is not None, f"Token --{fondo} no encontrado en Marea"

    contraste = razon_contraste(hexadecimal_a_rgb(hexadecimal_frente), hexadecimal_a_rgb(hexadecimal_fondo))
    assert contraste >= umbral, (
        f"Contraste insuficiente en Marea: --{frente} ({hexadecimal_frente}) sobre --{fondo} ({hexadecimal_fondo}) = "
        f"{contraste:.2f}:1 (requerido >= {umbral:.1f}:1)"
    )


def test_relieve_marea_por_diferencias_de_luminancia():
    """Verifica que el relieve neumórfico posea diferencias mínimas de luminancia relativa."""
    temas = analizar_tokens(RUTA_CSS)
    marea = temas["marea"]

    luminancia_pagina = luminancia_relativa(hexadecimal_a_rgb(marea["--bg-page"]))
    luminancia_panel = luminancia_relativa(hexadecimal_a_rgb(marea["--bg-panel"]))
    luminancia_elevada = luminancia_relativa(hexadecimal_a_rgb(marea["--bg-elevated"]))
    luminancia_entrada = luminancia_relativa(hexadecimal_a_rgb(marea["--input-bg"]))

    # Heurística 1: El panel debe ser notablemente más oscuro que la página (ΔL >= 0.08)
    diferencia_panel = luminancia_pagina - luminancia_panel
    assert diferencia_panel >= 0.08, (
        f"Relieve insuficiente entre --bg-page ({luminancia_pagina:.4f}) y --bg-panel ({luminancia_panel:.4f}): ΔL = {diferencia_panel:.4f} < 0.08"
    )

    # Heurística 2: El input debe ser claramente hundido respecto a la página (ΔL >= 0.15)
    diferencia_entrada = luminancia_pagina - luminancia_entrada
    assert diferencia_entrada >= 0.15, (
        f"Relieve insuficiente de hundimiento para --input-bg: ΔL = {diferencia_entrada:.4f} < 0.15"
    )

    # Heurística 3: El input debe ser más oscuro que el panel (ΔL >= 0.05)
    diferencia_panel_entrada = luminancia_panel - luminancia_entrada
    assert diferencia_panel_entrada >= 0.05, (
        f"El input debe ser más oscuro que el panel: ΔL = {diferencia_panel_entrada:.4f} < 0.05"
    )

    # Heurística 4: La superficie elevated debe ser más clara que la página (L_elevated > L_page)
    assert luminancia_elevada > luminancia_pagina, (
        f"La superficie --bg-elevated ({luminancia_elevada:.4f}) debe ser más clara que --bg-page ({luminancia_pagina:.4f})"
    )


def test_muestra_marea_declarada_cuatro_veces():
    """Verifica que las cuatro declaraciones de --swatch-marea sean exactamente #CFE3F0."""
    contenido = RUTA_CSS.read_text(encoding="utf-8")
    assert contenido.count("--swatch-marea: #CFE3F0;") >= 4, (
        f"Se esperaban al menos 4 declaraciones exactas de '--swatch-marea: #CFE3F0;', "
        f"se encontraron {contenido.count('--swatch-marea: #CFE3F0;')}"
    )


def test_tokens_papel_y_medianoche_conservados():
    """Verifica que los tokens de Papel y Medianoche permanezcan idénticos a su estado canónico."""
    temas = analizar_tokens(RUTA_CSS)
    papel = temas["papel"]
    medianoche = temas["medianoche"]

    papel_esperado = {
        "--bg-page": "#F2F0EB", "--bg-panel": "#EDEAE3",
        "--bg-elevated": "#F7F5F1", "--bg-calc-btn": "#F6F4EF",
        "--input-bg": "#E5E1D8", "--text-main": "#23262E",
        "--text-sec": "#5A6070",
        "--accent": "#1F6B64",
        "--accent-soft": "#D8E8E5",
        "--btn-primary-text": "#F7F5F1",
        "--focus-ring": "#1F6B64",
        "--error": "#B23A31",
        "--success": "#1B7046",
        "--warning": "#855A09",
    }
    _comprobar_tokens_papel(papel, papel_esperado)

    medianoche_esperada = {
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
    for k, v in medianoche_esperada.items():
        assert medianoche.get(k) == v, f"Token Medianoche {k} alterado: {medianoche.get(k)} != {v}"


def _comprobar_tokens_papel(papel, esperados):
    for k, v in esperados.items():
        assert papel.get(k) == v, f"Token Papel {k} alterado: {papel.get(k)} != {v}"
