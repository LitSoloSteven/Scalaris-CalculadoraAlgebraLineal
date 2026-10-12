"""Test estructural para verificar que ningún archivo en src/frontend y src/ai

utiliza nombres globales no definidos ni importados.
"""
from __future__ import annotations

import ast
import builtins
from pathlib import Path


NOMBRES_PREDEFINIDOS = set(dir(builtins)) | {
    "__file__",
    "__name__",
    "__doc__",
    "__package__",
    "__path__",
    "__builtins__",
    "__annotations__",
}


def reunir_nombres_enlazados(arbol: ast.AST) -> set[str]:
    """Reúne todos los nombres enlazados en cualquier parte del árbol sintáctico."""
    nombres = set(NOMBRES_PREDEFINIDOS)
    for nodo in ast.walk(arbol):
        nombres.update(_nombres_declarados(nodo))
        nombres.update(_nombres_importados(nodo))
    return nombres


def _nombres_declarados(nodo):
    if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        parametros = _nombres_parametros(nodo.args) if hasattr(nodo, "args") else set()
        return {nodo.name} | parametros
    if isinstance(nodo, ast.Lambda):
        return _nombres_parametros(nodo.args)
    if isinstance(nodo, ast.ExceptHandler):
        return {nodo.name} if nodo.name else set()
    if isinstance(nodo, (ast.Global, ast.Nonlocal)):
        return set(nodo.names)
    if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
        return {nodo.id}
    return set()


def _nombres_importados(nodo):
    if isinstance(nodo, ast.Import):
        return {referencia.asname or referencia.name.split(".")[0] for referencia in nodo.names}
    if isinstance(nodo, ast.ImportFrom):
        return {referencia.asname or referencia.name for referencia in nodo.names}
    return set()


def _nombres_parametros(argumentos):
    nombres = {argumento.arg for argumento in argumentos.posonlyargs + argumentos.args + argumentos.kwonlyargs}
    if argumentos.vararg:
        nombres.add(argumentos.vararg.arg)
    if argumentos.kwarg:
        nombres.add(argumentos.kwarg.arg)
    return nombres


def buscar_nombres_sin_enlace(ruta: Path) -> list[tuple[str, int, str]]:
    """Encuentra nombres en contexto Load que no estén enlazados en el archivo ni en builtins."""
    contenido = ruta.read_text(encoding="utf-8")
    arbol = ast.parse(contenido, filename=str(ruta))
    enlazados = reunir_nombres_enlazados(arbol)
    sin_enlace = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Load):
            if nodo.id not in enlazados:
                sin_enlace.append((ruta.as_posix(), nodo.lineno, nodo.id))
    return sin_enlace


def test_interfaz_y_asistente_sin_nombres_globales_sin_enlace():
    """Recorre todos los módulos de src/frontend y src/ai asegurando que todo nombre esté enlazado."""
    raiz = Path(__file__).resolve().parent.parent
    carpetas = [raiz / "src" / "frontend", raiz / "src" / "ai"]
    sin_enlace = []
    cantidad = 0
    for carpeta in carpetas:
        for ruta in carpeta.rglob("*.py"):
            cantidad += 1
            sin_enlace.extend(buscar_nombres_sin_enlace(ruta))
    assert cantidad > 0, "No se encontraron archivos .py para escanear"
    if sin_enlace:
        lineas = [f"{ruta}:{linea} -> '{nombre}'" for ruta, linea, nombre in sin_enlace]
        informe = "\n".join(lineas)
        raise AssertionError(
            f"Se encontraron {len(sin_enlace)} nombres no definidos/importados:\n{informe}"
        )


def test_detector_encuentra_importaciones_ausentes():
    """El detector identifica las importaciones ausentes de asyncio, json y html."""
    codigo_muestra = '''
def programar_actualizacion_contexto():
    async def _debounced():
        await asyncio.sleep(0.25)
    _debounced()

def _render_message(text):
    s = json.dumps(text)
    return html.escape(s)
'''
    arbol = ast.parse(codigo_muestra)
    enlazados = reunir_nombres_enlazados(arbol)
    ausentes = [
        nodo.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Name)
        and isinstance(nodo.ctx, ast.Load)
        and nodo.id not in enlazados
    ]

    assert "asyncio" in ausentes
    assert "json" in ausentes
    assert "html" in ausentes
