"""Patrones y comprobaciones comunes de textos de presentación."""
import re

PATRONES_VOSEO = [
    r'\bvos\b', r'\bpodés\b', r'\btenés\b', r'\bquerés\b',
    r'\bhacé\b', r'\bmirá\b', r'\bfijate\b', r'\bacá\b',
]


def comprobar_textos_sobrios(textos, patrones, contexto=""):
    """Comprueba cada texto recibido con las mismas restricciones de puntuación y voseo."""
    for texto in textos:
        assert "—" not in texto, f"Raya larga encontrada {contexto}: {texto}"
        assert "Oops" not in texto, f"Interjección encontrada {contexto}: {texto}"
        for patron in patrones:
            assert not re.search(patron, texto, re.IGNORECASE), f"Voseo '{patron}' {contexto}: {texto}"
