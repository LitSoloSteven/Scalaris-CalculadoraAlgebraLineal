"""Tuteo y texto de ayuda de la interfaz y del asistente."""
import re
from pathlib import Path
import pytest

PATRON_VOSEO = re.compile(
    r"\b(ingresá|añadí|escribí|presioná|pegá|preguntá|contactá|instalá|elegí|seleccioná|usá|probá|revisá)\b",
    re.IGNORECASE
)


def _reunir_archivos():
    raices = [Path("src/frontend"), Path("src/ai")]
    archivos = []
    for raiz in raices:
        for p in raiz.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".js"):
                archivos.append(p)
    return archivos


def test_interfaz_y_asistente_sin_voseo():
    """Verifica que ningún archivo en src/frontend o src/ai contenga formas voseo prohibidas."""
    archivos = _reunir_archivos()
    assert len(archivos) > 0, "No se encontraron archivos en src/frontend o src/ai"

    infracciones = []
    for ruta_archivo in archivos:
        texto = ruta_archivo.read_text(encoding="utf-8")
        coincidencias = PATRON_VOSEO.findall(texto)
        if coincidencias:
            infracciones.append(f"{ruta_archivo}: {coincidencias}")

    assert not infracciones, f"Se encontraron formas voseo en los siguientes archivos:\n" + "\n".join(infracciones)


def test_ayuda_matriz_cuadrada_usa_limite_dinamico():
    """Verifica que el panel de matriz cuadrada use el límite dinámico en el texto de ayuda."""
    archivo_panel = Path("src/frontend/componentes/panel_matriz_cuadrada.py")
    assert archivo_panel.exists()
    contenido = archivo_panel.read_text(encoding="utf-8")
    assert "Máx. 50×50" not in contenido, "square_matrix_panel.py todavía contiene 'Máx. 50×50' hardcodeado"
    assert "DIMENSION_MAXIMA_INVERSA" in contenido
    assert "Pega desde Excel" in contenido
