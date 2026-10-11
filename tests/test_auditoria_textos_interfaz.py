"""Auditoría de textos visibles de la interfaz y del asistente.

Verifica mediante análisis estático de AST que ninguna constante de cadena
(excluyendo docstrings) en src/frontend y src/ai contenga raya larga, 'Oops' ni
formas de voseo no autorizadas.
Verifica además la presencia de 'Hola, soy Glosa.' y la ausencia de '¡Hola! Soy Glosa.',
así como la alineación de nombres con navigation.py.
"""
import ast
import os
import re
from src.frontend.navigation import TOOLS, PILLARS


def _es_docstring(node: ast.Constant, parent: ast.AST) -> bool:
    """Detecta si un nodo ast.Constant representa el docstring del nodo padre."""
    if isinstance(parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if parent.body and isinstance(parent.body[0], ast.Expr) and parent.body[0].value is node:
            return True
    return False


def test_textos_sin_raya_larga_interjecciones_ni_voseo():
    """Ninguna constante de cadena en src/frontend y src/ai contiene '—', 'Oops' ni voseo."""
    voseo_patterns = [
        r'\bvos\b',
        r'\bpodés\b',
        r'\btenés\b',
        r'\bquerés\b',
        r'\bhacé\b',
        r'\bmirá\b',
        r'\bfijate\b',
        r'\bacá\b',
    ]
    bad_substrings = ['—', 'Oops']

    violations = []

    for root_dir in ['src/frontend', 'src/ai']:
        for root, _, files in os.walk(root_dir):
            for f in files:
                if not f.endswith('.py'):
                    continue
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as fp:
                    try:
                        tree = ast.parse(fp.read(), filename=path)
                    except Exception as e:
                        violations.append(f"Error parseando {path}: {e}")
                        continue

                violations.extend(_infracciones_cadenas(tree, path, bad_substrings, voseo_patterns))

    assert not violations, "Violaciones de copy detectadas:\n" + "\n".join(violations)


def _infracciones_cadenas(arbol, ruta, fragmentos, patrones):
    infracciones = []
    for padre in ast.walk(arbol):
        for hijo in ast.iter_child_nodes(padre):
            if isinstance(hijo, ast.Constant) and isinstance(hijo.value, str):
                if _es_docstring(hijo, padre):
                    continue
                valor = hijo.value
                relativa = os.path.relpath(ruta).replace('\\', '/')
                # La migración del historial reconoce el saludo anterior del asistente.
                if 'ai_panel.py' in relativa and ('—' in valor or 'Tutor IA' in valor):
                    continue
                for fragmento in fragmentos:
                    if fragmento in valor:
                        infracciones.append(f"{relativa}:{hijo.lineno} contiene {repr(fragmento)}: {valor[:60]}")
                for patron in patrones:
                    if re.search(patron, valor, re.IGNORECASE):
                        infracciones.append(f"{relativa}:{hijo.lineno} coincide con patrón voseo {patron}: {valor[:60]}")
    return infracciones


def test_saludo_glosa_unificado():
    """El saludo de Glosa conserva tuteo y puntuación sobria."""
    dock_file = os.path.join('src', 'frontend', 'componentes', 'glosa_bitacora.py')
    with open(dock_file, 'r', encoding='utf-8') as fp:
        content = fp.read()

    assert "¡Hola! Soy Glosa." not in content, "Aún contiene '¡Hola! Soy Glosa.'"
    assert "Hola, soy Glosa." in content, "No contiene 'Hola, soy Glosa.'"


def test_nombres_navegacion_alineados():
    """Verifica la alineación de nombres con navigation.py."""
    expected_tools = {
        "/algebra-lineal/sistemas": "Sistemas de ecuaciones",
        "/algebra-lineal/inversa": "Matriz inversa",
        "/algebra-lineal/matrices": "Matrices",
        "/algebra-lineal/vectores": "Vectores",
        "/visualizador": "Rectas, planos y vectores",
        "/utilidades/bases": "Conversor de bases",
        "/utilidades/romanos": "Números romanos",
    }

    tool_by_route = {t.route: t.name for t in TOOLS}
    for route, expected_name in expected_tools.items():
        assert route in tool_by_route, f"Ruta {route} no encontrada en TOOLS"
        assert tool_by_route[route] == expected_name, (
            f"Ruta {route} tiene nombre {tool_by_route[route]}, se esperaba {expected_name}"
        )
