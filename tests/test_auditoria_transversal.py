"""Auditoría global de idioma, comentarios y secuencias repetidas de producción."""
import ast
import io
import re
import tokenize

import pytest

from tests.comun import RAIZ
from tests.comun_duplicacion import duplicaciones_python
from tests.comun_idioma import declaraciones_propias, ingles_propio
from tests.comun_javascript_embebido import fuentes_javascript
from tests.comun_transversal import analizar_fuentes_cliente

FUENTES_PYTHON = {ruta.relative_to(RAIZ).as_posix(): ruta.read_text(encoding='utf-8')
                  for ruta in (RAIZ / 'src').rglob('*.py')}
PATRON_PROHIBIDO = re.compile(r'\b(?:TODO|FIXME|HACK|XXX|corregido|modificado|bug fix)\b|—|^[\s#/*-]*[=*#-]{3,}', re.I)


@pytest.fixture(scope='module')
def analisis_cliente():
    """Analiza recursos y JavaScript embebido de producción con Acorn incluido en Node."""
    rutas = sorted(ruta for ruta in (RAIZ / 'src').rglob('*')
                   if ruta.is_file() and ruta.suffix in {'.py', '.js', '.html'})
    return analizar_fuentes_cliente(fuentes_javascript(rutas))


def test_identificadores_propios_python_en_espanol():
    """Comprueba variables y parámetros que no cubría el vocabulario histórico reducido."""
    infracciones = [(ruta, linea, nombre) for ruta, texto in FUENTES_PYTHON.items()
                    for nombre, linea in declaraciones_propias(ast.parse(texto))
                    if not nombre.isascii() or ingles_propio(nombre, ruta)]
    assert not infracciones, infracciones


def test_identificadores_propios_cliente_en_espanol(analisis_cliente):
    """Comprueba declaraciones cliente de recursos, HTML y emisiones Python sin ejecutarlas."""
    infracciones = [(fuente['ruta'], nombre['linea'], nombre['nombre'])
                    for fuente in analisis_cliente['resultados'] for nombre in fuente['nombres']
                    if not nombre['nombre'].isascii() or ingles_propio(nombre['nombre'], fuente['ruta'])]
    assert not infracciones, infracciones


def _comprobar_comentario(texto, ubicacion):
    assert len(texto.strip().splitlines()) <= 2, ubicacion
    assert not PATRON_PROHIBIDO.search(texto), (ubicacion, texto)


def test_documentacion_y_comentarios_python_sobrios():
    """Comprueba comentarios y docstrings de todos los módulos de producción."""
    for ruta, texto in FUENTES_PYTHON.items():
        for token in tokenize.generate_tokens(io.StringIO(texto).readline):
            if token.type == tokenize.COMMENT:
                _comprobar_comentario(token.string, (ruta, token.start[0]))
        _comprobar_documentacion(ruta, texto)


def _comprobar_documentacion(ruta, texto):
    for nodo in ast.walk(ast.parse(texto)):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            documento = ast.get_docstring(nodo)
            if documento:
                _comprobar_comentario(documento, (ruta, getattr(nodo, 'lineno', 1)))


def test_comentarios_cliente_sobrios(analisis_cliente):
    """Comprueba comentarios JavaScript reales, también en código embebido."""
    for fuente in analisis_cliente['resultados']:
        for comentario in fuente['comentarios']:
            _comprobar_comentario(comentario['value'], (fuente['ruta'], comentario['start']))


def test_comentarios_estilos_y_plantillas_sobrios():
    """Comprueba bloques de comentario CSS y HTML sin confundir colores ni URLs."""
    for ruta in (RAIZ / 'src').rglob('*'):
        if ruta.suffix not in {'.css', '.html'}:
            continue
        patron = r'/\*[\s\S]*?\*/' if ruta.suffix == '.css' else r'<!--[\s\S]*?-->'
        for comentario in re.findall(patron, ruta.read_text(encoding='utf-8')):
            _comprobar_comentario(comentario, ruta)


def test_sin_bloques_python_repetidos():
    """Detecta la segunda aparición de cinco líneas, incluso con locales renombrados."""
    assert not duplicaciones_python(FUENTES_PYTHON)


def test_sin_bloques_cliente_repetidos(analisis_cliente):
    """Detecta bloques JavaScript repetidos entre recursos y emisiones de producción."""
    assert not analisis_cliente['duplicaciones'], analisis_cliente['duplicaciones']
