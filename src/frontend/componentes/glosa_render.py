"""Renderizado seguro de respuestas de Glosa con escape de etiquetas y bloques pre."""
from __future__ import annotations

import html
import re


def render_glosa_text(text: str) -> str:
    """Escapa HTML y procesa bloques de código con triple backtick para presentación segura.

    El texto general se coloca en contenedores con ajuste de línea y palabras largas,
    mientras los bloques de código delimitados por tres acentos graves se aíslan en pre.
    """
    if not text:
        return ""

    escaped = html.escape(text)
    partes = re.split(r"```(.*?)```", escaped, flags=re.DOTALL)

    salida: list[str] = []
    for indice, bloque in enumerate(partes):
        if indice % 2 == 1:
            salida.append(f'<pre class="glosa-pre"><code>{bloque}</code></pre>')
        elif bloque:
            salida.append(f'<div class="glosa-texto-bloque">{bloque}</div>')

    return "".join(salida)
