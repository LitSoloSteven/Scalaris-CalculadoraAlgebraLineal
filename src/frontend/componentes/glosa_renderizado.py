"""Renderizado seguro de respuestas de Glosa con escape de etiquetas y bloques pre."""
from __future__ import annotations

import html
import re


def renderizar_texto_glosa(texto: str) -> str:
    """Devuelve HTML escapado con ajuste de línea y palabras para el texto de Glosa.
    Los bloques delimitados por tres acentos graves se aíslan en elementos pre."""
    if not texto:
        return ""

    texto_escapado = html.escape(texto)
    partes = re.split(r"```(.*?)```", texto_escapado, flags=re.DOTALL)

    salida: list[str] = []
    for indice, bloque in enumerate(partes):
        if indice % 2 == 1:
            salida.append(f'<pre class="glosa-pre"><code>{bloque}</code></pre>')
        elif bloque:
            salida.append(f'<div class="glosa-texto-bloque">{bloque}</div>')

    return "".join(salida)
