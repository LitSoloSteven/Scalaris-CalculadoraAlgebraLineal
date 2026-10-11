"""Muestras de color de cada tema y sus declaraciones CSS."""
import re
from pathlib import Path
import pytest

from tests.comun_estilos import analizar_tokens

CSS_PATH = Path("src/frontend/assets/css/tokens.css")

EXPECTED_SWATCHES = {
    "--swatch-papel": "#F2F0EB",
    "--swatch-marea": "#CFE3F0",
    "--swatch-medianoche": "#082338",
}


def test_muestras_coinciden_con_fondo_de_cada_tema():
    """Cada swatch debe coincidir exactamente con el color de fondo (--bg-page) de su tema."""
    themes = analizar_tokens(CSS_PATH, pasadas=1, exigir_cierre=False)

    assert themes["papel"]["--swatch-papel"] == themes["papel"]["--bg-page"]
    assert themes["marea"]["--swatch-marea"] == themes["marea"]["--bg-page"]
    assert themes["medianoche"]["--swatch-medianoche"] == themes["medianoche"]["--bg-page"]


def test_muestras_definidas_en_raiz_y_todos_los_temas():
    """Verifica que los tres swatches esten declarados en :root y en cada uno de los bloques de tema."""
    content = CSS_PATH.read_text(encoding="utf-8")

    # Cada token swatch aparece declarado al menos 4 veces (:root y los 3 temas)
    for swatch, val in EXPECTED_SWATCHES.items():
        assert content.count(f"{swatch}: {val};") >= 4

    # Verificar presencia explícita en los 4 bloques temáticos principales de tokens.css
    all_blocks = re.findall(r"(:root[^{]*)\{([^}]+)\}", content, re.DOTALL)
    blocks = [b for b in all_blocks if "--swatch-papel" in b[1]]
    assert len(blocks) == 4, f"Se esperaban 4 bloques principales en el encabezado, se encontraron {len(blocks)}"

    for sel, body in blocks:
        for swatch, val in EXPECTED_SWATCHES.items():
            assert f"{swatch}: {val};" in body, (
                f"Token {swatch} con valor {val} no encontrado en bloque {sel.strip()}"
            )
