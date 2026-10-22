"""Regresiones del análisis sintáctico empleado por la auditoría global."""
import ast
from tests.comun_auditoria import (
    calcular_anidamiento_y_complejidad, cadenas_presentacion,
    comentarios_y_documentacion, declaraciones_publicas, nombres_parametros,
)


def test_firma_incluye_parametros_exclusivos_y_variadicos():
    """Ninguna forma de declarar parámetros elude el límite de la firma."""
    nodo = ast.parse("def funcion(a, b, c, d, e, /, *valores, f, g, **opciones): pass").body[0]
    assert nombres_parametros(nodo) == ["a", "b", "c", "d", "e", "f", "g", "valores", "opciones"]


def test_documentacion_incluye_metodos_y_funciones_asincronas():
    """Las declaraciones públicas se revisan también dentro de clases."""
    arbol = ast.parse("class Cliente:\n async def enviar(self): pass\n def _interno(self): pass")
    assert [nodo.name for nodo in declaraciones_publicas(arbol)] == ["Cliente", "enviar"]


def test_ramas_elif_comparten_nivel_y_suman_decisiones():
    """El análisis diferencia cadenas de alternativas de bloques anidados."""
    nodo = ast.parse("def elegir(valor):\n if valor == 1: pass\n elif valor == 2: pass\n elif valor == 3: pass").body[0]
    assert calcular_anidamiento_y_complejidad(nodo) == (1, 4)
    anidado = ast.parse("def elegir(valor):\n if valor:\n  if valor > 2:\n   if valor > 3: pass").body[0]
    assert calcular_anidamiento_y_complejidad(anidado) == (3, 4)


def test_comentarios_y_docstrings_no_confunden_muestras_de_prueba():
    """Los datos esperados quedan separados de comentarios y documentación."""
    contenido = '"""Documentación real."""\n# Motivo real\npatron = "TODO: muestra"'
    assert comentarios_y_documentacion(contenido) == ["# Motivo real", "Documentación real."]


def test_condicion_dentro_de_else_conserva_anidamiento_real():
    """Un bloque if dentro de else no se interpreta como una rama elif."""
    nodo = ast.parse("def elegir(valor):\n if valor: pass\n else:\n  if valor > 1: pass").body[0]
    assert calcular_anidamiento_y_complejidad(nodo) == (2, 3)


def test_cadenas_presentacion_separan_expectativas_y_html_renderizado():
    """La auditoría conserva el contenido renderizado aunque esté en una prueba."""
    arbol = ast.parse('assert "style=" not in fuente\nui.html(\'<div style="color:red"></div>\')')
    assert cadenas_presentacion(arbol, es_prueba=True) == ['<div style="color:red"></div>']
    assert "style=" in cadenas_presentacion(arbol, es_prueba=False)
