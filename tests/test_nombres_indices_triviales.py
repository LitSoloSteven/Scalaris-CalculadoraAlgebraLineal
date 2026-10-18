"""Regresión de abreviaturas propias fuera de los índices numéricos inspeccionados."""
import ast
from tests.comun import RAIZ


def test_solo_indices_triviales_conservan_letras_sueltas():
    """Incluye parámetros, variables y excepciones que el vocabulario inglés no detecta."""
    indices_inspeccionados = {"i", "j", "r", "c", "f", "k"}
    infracciones = []
    for ruta in (RAIZ / "src").rglob("*.py"):
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
            nombre = _nombre_declarado(nodo)
            if nombre and len(nombre) == 1 and nombre.isalpha() and nombre not in indices_inspeccionados:
                infracciones.append((str(ruta), nodo.lineno, nombre))
    assert not infracciones, infracciones


def _nombre_declarado(nodo):
    if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
        return nodo.id
    if isinstance(nodo, ast.arg):
        return nodo.arg
    if isinstance(nodo, ast.ExceptHandler):
        return nodo.name
    return None
