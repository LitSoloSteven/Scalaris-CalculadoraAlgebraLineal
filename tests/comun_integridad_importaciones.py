"""Resolución de importaciones internas mediante AST, incluidos bloques diferidos."""
import ast
import importlib
from pathlib import Path

from tests.comun import RAIZ


def referencias_importadas(ruta: Path, contenido: str | None = None) -> list[tuple]:
    """Recoge módulos y símbolos internos con su línea y paquete de origen."""
    texto = contenido if contenido is not None else ruta.read_text(encoding="utf-8")
    partes = list(ruta.relative_to(RAIZ).with_suffix("").parts)
    paquete = ".".join(partes[:-1])
    referencias = []
    for nodo in ast.walk(ast.parse(texto)):
        referencias.extend(_referencias_nodo(nodo, paquete))
    return referencias


def _referencias_nodo(nodo: ast.AST, paquete: str) -> list[tuple]:
    if isinstance(nodo, ast.Import):
        return _referencias_modulos(nodo)
    if not isinstance(nodo, ast.ImportFrom):
        return []
    modulo = nodo.module or ""
    if nodo.level:
        modulo = importlib.util.resolve_name("." * nodo.level + modulo, paquete)
    if modulo != "src" and not modulo.startswith("src."):
        return []
    return [(nodo.lineno, modulo, elemento.name) for elemento in nodo.names]


def _referencias_modulos(nodo: ast.Import) -> list[tuple]:
    return [(nodo.lineno, elemento.name, None) for elemento in nodo.names
            if elemento.name == "src" or elemento.name.startswith("src.")]


def resolver_referencia(modulo: str, simbolo: str | None) -> str | None:
    """Devuelve el error de un import real; acepta submódulos y exportaciones."""
    try:
        importado = importlib.import_module(modulo)
        if simbolo is None:
            return None
        if simbolo == "*":
            return _comprobar_exportaciones(importado)
        if hasattr(importado, simbolo):
            return None
        importlib.import_module(f"{modulo}.{simbolo}")
    except (ImportError, AttributeError, ValueError) as error:
        return f"{modulo}:{simbolo}: {type(error).__name__}: {error}"
    return None


def _comprobar_exportaciones(modulo) -> str | None:
    for simbolo in getattr(modulo, "__all__", ()):
        if not hasattr(modulo, simbolo):
            return f"{modulo.__name__}: exportación ausente {simbolo}"
    return None


def errores_importaciones(rutas: list[Path]) -> list[str]:
    """Resuelve todas las referencias recogidas sin detenerse en el primer fallo."""
    errores = []
    for ruta in rutas:
        for linea, modulo, simbolo in referencias_importadas(ruta):
            error = resolver_referencia(modulo, simbolo)
            if error:
                errores.append(f"{ruta.relative_to(RAIZ)}:{linea}: {error}")
    return errores
