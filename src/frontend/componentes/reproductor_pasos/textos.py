"""Conversión de expresiones LaTeX a descripciones de procedimiento en texto plano."""
import html
import re


def formatear_descripcion_html(texto: str) -> str:
    """Escapa el texto y convierte potencias, subíndices y productos a HTML seguro."""
    contenido = html.escape(str(texto))
    contenido = contenido.replace("AA^{-1}", "A·A^{-1}").replace("A^{-1}A", "A^{-1}·A")
    contenido = contenido.replace(r"\cdot", "·").replace("^T", "ᵀ")
    patron = re.compile(r"([\^_])\{([^{}]*)\}")
    while patron.search(contenido):
        contenido = patron.sub(_convertir_indice, contenido)
    return contenido


def _convertir_indice(coincidencia: re.Match) -> str:
    """Envuelve únicamente contenido ya escapado en etiquetas fijas."""
    etiqueta = "sup" if coincidencia[1] == "^" else "sub"
    return f"<{etiqueta}>{coincidencia[2]}</{etiqueta}>"


def limpiar_latex_plano(texto: str) -> str:
    """Elimina comandos y espaciado LaTeX y devuelve una descripción textual compacta."""
    contenido = re.sub(r"\\text\{([^}]*)\}", r"\1", str(texto))
    contenido = contenido.replace(r"\implies", "=>").replace(r"\;", " ").replace(r"\\", " ")
    return " ".join(re.sub(r"[{}\\]", "", contenido).split())
