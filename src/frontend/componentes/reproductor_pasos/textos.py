"""Conversión de expresiones LaTeX a descripciones de procedimiento en texto plano."""
import re


def limpiar_latex_plano(texto: str) -> str:
    """Elimina comandos y espaciado LaTeX y devuelve una descripción textual compacta."""
    contenido = re.sub(r"\\text\{([^}]*)\}", r"\1", str(texto))
    contenido = contenido.replace(r"\implies", "=>").replace(r"\;", " ").replace(r"\\", " ")
    return " ".join(re.sub(r"[{}\\]", "", contenido).split())
