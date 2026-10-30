"""Conversión de expresiones LaTeX a descripciones de procedimiento en texto plano."""
import html
import re

COMPROBACION_PROPIEDAD = "Propiedad por comprobar"
COMPROBACION_CONTEXTO_INVERSA = (
    "Multiplicamos A por A⁻¹ y comparamos con I; cada celda es una fila de A "
    "por una columna de A⁻¹."
)
COMPROBACION_CONTEXTO_PRODUCTO = (
    "Multiplicamos las matrices de la propiedad y comparamos con la matriz esperada; "
    "cada celda es una fila de la primera matriz por una columna de la segunda."
)
COMPROBACION_CORRECTA = "Correcto"
COMPROBACION_INCORRECTA = "Incorrecto"
COMPROBACION_FILA = "Fila {fila}"
COMPROBACION_CELDA_GUIA = r"C_{1,1}=\text{fila 1 por columna 1}"
MATEMATICAS_DESPLAZAMIENTO = "Fórmula matemática; usa las flechas para desplazarte en horizontal"


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
