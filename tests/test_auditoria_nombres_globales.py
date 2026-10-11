"""Test estructural para verificar que ningún archivo en src/frontend y src/ai

utiliza nombres globales no definidos ni importados.
"""
from __future__ import annotations

import ast
import builtins
from pathlib import Path


BUILTIN_NAMES = set(dir(builtins)) | {
    "__file__",
    "__name__",
    "__doc__",
    "__package__",
    "__path__",
    "__builtins__",
    "__annotations__",
}


def reunir_nombres_enlazados(tree: ast.AST) -> set[str]:
    """Reúne todos los nombres enlazados en cualquier parte del árbol sintáctico."""
    bound = set(BUILTIN_NAMES)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
            if hasattr(node, "args"):
                bound.update(_nombres_parametros(node.args))

        elif isinstance(node, ast.Lambda):
            bound.update(_nombres_parametros(node.args))

        elif isinstance(node, ast.Import):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound.add(alias.asname or alias.name)

        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                bound.add(node.name)

        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                bound.add(name)

        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)

    return bound


def _nombres_parametros(argumentos):
    nombres = {argumento.arg for argumento in argumentos.posonlyargs + argumentos.args + argumentos.kwonlyargs}
    if argumentos.vararg:
        nombres.add(argumentos.vararg.arg)
    if argumentos.kwarg:
        nombres.add(argumentos.kwarg.arg)
    return nombres


def buscar_nombres_sin_enlace(file_path: Path) -> list[tuple[str, int, str]]:
    """Encuentra nombres en contexto Load que no estén enlazados en el archivo ni en builtins."""
    content = file_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(file_path))
    bound = reunir_nombres_enlazados(tree)

    unbound = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in bound:
                unbound.append((file_path.as_posix(), node.lineno, node.id))

    return unbound


def test_interfaz_y_asistente_sin_nombres_globales_sin_enlace():
    """Recorre todos los módulos de src/frontend y src/ai asegurando que todo nombre esté enlazado."""
    project_root = Path(__file__).resolve().parent.parent
    target_dirs = [project_root / "src" / "frontend", project_root / "src" / "ai"]

    all_unbound = []
    scanned_count = 0

    for target_dir in target_dirs:
        for py_path in target_dir.rglob("*.py"):
            scanned_count += 1
            unbound = buscar_nombres_sin_enlace(py_path)
            all_unbound.extend(unbound)

    assert scanned_count > 0, "No se encontraron archivos .py para escanear"

    if all_unbound:
        lines = [f"{p}:{lineno} -> '{name}'" for p, lineno, name in all_unbound]
        report = "\n".join(lines)
        raise AssertionError(
            f"Se encontraron {len(all_unbound)} nombres no definidos/importados:\n{report}"
        )


def test_detector_encuentra_importaciones_ausentes():
    """El detector identifica las importaciones ausentes de asyncio, json y html."""
    sample_code = '''
def programar_actualizacion_contexto():
    async def _debounced():
        await asyncio.sleep(0.25)
    _debounced()

def _render_message(text):
    s = json.dumps(text)
    return html.escape(s)
'''
    tree = ast.parse(sample_code)
    bound = reunir_nombres_enlazados(tree)
    missing = [
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id not in bound
    ]

    assert "asyncio" in missing
    assert "json" in missing
    assert "html" in missing
