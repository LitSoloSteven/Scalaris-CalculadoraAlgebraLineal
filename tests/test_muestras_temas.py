"""Muestras de color de cada tema y sus declaraciones CSS."""
import re
from pathlib import Path
import pytest

from tests.comun_estilos import analizar_tokens

RUTA_CSS = Path("src/frontend/recursos/css/tokens.css")

MUESTRAS_ESPERADAS = {
    "--swatch-papel": "#F2F0EB",
    "--swatch-marea": "#CFE3F0",
    "--swatch-medianoche": "#082338",
}


def test_muestras_coinciden_con_fondo_de_cada_tema():
    """Cada swatch debe coincidir exactamente con el color de fondo (--bg-page) de su tema."""
    temas = analizar_tokens(RUTA_CSS, pasadas=1, exigir_cierre=False)

    assert temas["papel"]["--swatch-papel"] == temas["papel"]["--bg-page"]
    assert temas["marea"]["--swatch-marea"] == temas["marea"]["--bg-page"]
    assert temas["medianoche"]["--swatch-medianoche"] == temas["medianoche"]["--bg-page"]


def test_muestras_definidas_en_raiz_y_todos_los_temas():
    """Verifica que los tres swatches esten declarados en :root y en cada uno de los bloques de tema."""
    contenido = RUTA_CSS.read_text(encoding="utf-8")

    # Cada token swatch aparece declarado al menos 4 veces (:root y los 3 temas)
    for muestra, valor in MUESTRAS_ESPERADAS.items():
        assert contenido.count(f"{muestra}: {valor};") >= 4

    # Verificar presencia explícita en los 4 bloques temáticos principales de tokens.css
    todos_bloques = re.findall(r"(:root[^{]*)\{([^}]+)\}", contenido, re.DOTALL)
    bloques = [b for b in todos_bloques if "--swatch-papel" in b[1]]
    assert len(bloques) == 4, f"Se esperaban 4 bloques principales en el encabezado, se encontraron {len(bloques)}"

    for selector, cuerpo in bloques:
        for muestra, valor in MUESTRAS_ESPERADAS.items():
            assert f"{muestra}: {valor};" in cuerpo, (
                f"Token {muestra} con valor {valor} no encontrado en bloque {selector.strip()}"
            )
