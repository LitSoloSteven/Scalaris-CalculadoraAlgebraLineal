"""Auditoría de textos visibles, saludo del asistente y nombres de navegación."""
import ast
import os
import re
from src.frontend.navigation import TOOLS
from tests.comun_recorrido_codigo import recorrer_archivos_codigo, pares_padre_hijo
from tests.comun_textos import PATRONES_VOSEO


def _es_docstring(nodo: ast.Constant, padre: ast.AST) -> bool:
    """Comprueba si el literal coincide con la primera expresión de una declaración."""
    if isinstance(padre, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if padre.body and isinstance(padre.body[0], ast.Expr) and padre.body[0].value is nodo:
            return True
    return False


def test_textos_sin_raya_larga_interjecciones_ni_voseo():
    """Las constantes de interfaz y asistente mantienen puntuación sobria y tuteo."""
    fragmentos = ['—', 'Oops']
    infracciones = []
    for ruta in recorrer_archivos_codigo(['src/frontend', 'src/ai'], ('.py',)):
        infracciones.extend(_infracciones_archivo(ruta, fragmentos, PATRONES_VOSEO))
    assert not infracciones, "Infracciones de textos detectadas:\n" + "\n".join(infracciones)


def _infracciones_archivo(ruta, fragmentos, patrones):
    contenido = ruta.read_text(encoding='utf-8')
    try:
        arbol = ast.parse(contenido, filename=str(ruta))
    except Exception as error:
        return [f"Error analizando {ruta}: {error}"]
    return _infracciones_cadenas(arbol, ruta, fragmentos, patrones)


def _infracciones_cadenas(arbol, ruta, fragmentos, patrones):
    infracciones = []
    relativa = os.path.relpath(ruta).replace('\\', '/')
    for padre, hijo in pares_padre_hijo(arbol):
        if not isinstance(hijo, ast.Constant) or not isinstance(hijo.value, str):
            continue
        if _es_docstring(hijo, padre) or _es_saludo_anterior(relativa, hijo.value):
            continue
        infracciones.extend(_infracciones_literal(relativa, hijo, fragmentos, patrones))
    return infracciones


def _es_saludo_anterior(ruta, valor):
    # La migración del historial reconoce el saludo anterior del asistente.
    return 'ai_panel.py' in ruta and ('—' in valor or 'Tutor IA' in valor)


def _infracciones_literal(ruta, nodo, fragmentos, patrones):
    valor = nodo.value
    infracciones = []
    for fragmento in fragmentos:
        if fragmento in valor:
            infracciones.append(f"{ruta}:{nodo.lineno} contiene {repr(fragmento)}: {valor[:60]}")
    for patron in patrones:
        if re.search(patron, valor, re.IGNORECASE):
            infracciones.append(f"{ruta}:{nodo.lineno} coincide con patrón voseo {patron}: {valor[:60]}")
    return infracciones


def test_saludo_glosa_unificado():
    """El saludo de Glosa conserva tuteo y puntuación sobria."""
    ruta = os.path.join('src', 'frontend', 'componentes', 'glosa_bitacora.py')
    with open(ruta, 'r', encoding='utf-8') as archivo:
        contenido = archivo.read()
    assert "¡Hola! Soy Glosa." not in contenido, "Aún contiene '¡Hola! Soy Glosa.'"
    assert "Hola, soy Glosa." in contenido, "No contiene 'Hola, soy Glosa.'"


def test_nombres_navegacion_alineados():
    """Verifica la alineación de nombres con navigation.py."""
    herramientas_esperadas = {
        "/algebra-lineal/sistemas": "Sistemas de ecuaciones",
        "/algebra-lineal/inversa": "Matriz inversa",
        "/algebra-lineal/matrices": "Matrices",
        "/algebra-lineal/vectores": "Vectores",
        "/visualizador": "Rectas, planos y vectores",
        "/utilidades/bases": "Conversor de bases",
        "/utilidades/romanos": "Números romanos",
    }

    herramientas_por_ruta = {herramienta.route: herramienta.name for herramienta in TOOLS}
    for ruta, nombre_esperado in herramientas_esperadas.items():
        assert ruta in herramientas_por_ruta, f"Ruta {ruta} no encontrada en el catálogo"
        assert herramientas_por_ruta[ruta] == nombre_esperado, (
            f"Ruta {ruta} tiene nombre {herramientas_por_ruta[ruta]}, se esperaba {nombre_esperado}"
        )
