"""Auditoría de límites, documentación, idioma, comentarios, CSS y cadenas embebidas."""
import ast
import re
from tests.comun import RAIZ
from tests.rutas_auditadas import RUTAS_AUDITADAS
from tests.comun_auditoria import (
    calcular_anidamiento_y_complejidad, cadenas_presentacion,
    comentarios_y_documentacion, declaraciones_publicas, nombres_parametros,
)

PALABRAS_INGLES_PROHIBIDAS = {
    'solver', 'solvers', 'matrix', 'rows', 'cols', 'solve',
    'step', 'steps', 'controller', 'view', 'components', 'models',
}
EXCEPCIONES_E4_PERMITIDAS = {
    'app', 'main', 'ui', 'props', 'classes', 'style', 'value',
    'on_click', 'on_change', 'slot', 'row', 'column', 'card',
    'button', 'input', 'label', 'icon', 'dialog', 'select',
}
PATRONES_COMENTARIOS_PROHIBIDOS = [
    re.compile(r'^\s*#\s*[-=*#]{3,}', re.MULTILINE),
    re.compile(r'\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE),
    re.compile(r'\b(F8[a-z]?|F4|F9[a-z]?|LIT-\d+|Paso\s+\d+)\b', re.IGNORECASE),
    re.compile(r'[\U00010000-\U0010ffff]', re.UNICODE),
    re.compile(r'—'),
]


def test_sin_marcadores_de_conflicto_global():
    """Verifica que ningún archivo de código contenga marcadores de git."""
    extensiones = {'.py', '.js', '.css', '.html'}
    patron = re.compile(r'^(<{7}|={7}|>{7})(?:[ \t\r\n]|$)', re.MULTILINE)
    archivos = [
        p for p in RAIZ.glob('src/**/*') if p.is_file() and p.suffix in extensiones
    ] + [
        p for p in RAIZ.glob('tests/**/*.py') if p.is_file()
    ]
    for ruta in archivos:
        contenido = ruta.read_text(encoding='utf-8', errors='ignore')
        assert not patron.findall(contenido), f'Marcador de conflicto en {ruta.name}'


def test_limites_tamanio_y_complejidad():
    """Audita límites de 300 líneas por archivo, 40 por función y 200 por clase."""
    for ruta in RUTAS_AUDITADAS:
        if not ruta.exists():
            continue
        lineas = ruta.read_text(encoding='utf-8').splitlines()
        assert len(lineas) <= 300, f'{ruta.name} tiene {len(lineas)} líneas (máximo 300)'
        if ruta.suffix != '.py':
            continue
        arbol = ast.parse('\n'.join(lineas), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ClassDef):
                alt = (nodo.end_lineno or nodo.lineno) - nodo.lineno + 1
                assert alt <= 200, f'{ruta.name}:{nodo.name} tiene {alt} líneas (máximo 200)'
            elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                alt = (nodo.end_lineno or nodo.lineno) - nodo.lineno + 1
                assert alt <= 40, f'{ruta.name}:{nodo.name} tiene {alt} líneas (máximo 40)'
                parametros = nombres_parametros(nodo)
                assert len(parametros) <= 5, f'{ruta.name}:{nodo.name} tiene {len(parametros)} parámetros'
                anid, comp = calcular_anidamiento_y_complejidad(nodo)
                assert anid <= 3, f'{ruta.name}:{nodo.name} anidamiento {anid} (máximo 3)'
                assert comp <= 10, f'{ruta.name}:{nodo.name} complejidad {comp} (máximo 10)'


def test_docstrings_publicos():
    """Verifica que toda clase y función pública posea docstring no vacío."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != '.py' or not ruta.exists():
            continue
        arbol = ast.parse(ruta.read_text(encoding='utf-8'), filename=str(ruta))
        for nodo in declaraciones_publicas(arbol):
            doc = ast.get_docstring(nodo)
            assert doc and doc.strip(), f'Sin docstring público en {ruta.name}:{nodo.name}'


def test_identificadores_idioma_y_ascii():
    """Comprueba identificadores en ASCII y ausencia de nombres ingleses prohibidos."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != '.py' or not ruta.exists():
            continue
        arbol = ast.parse(ruta.read_text(encoding='utf-8'), filename=str(ruta))
        for nodo in ast.walk(arbol):
            nombre = getattr(nodo, 'id', None) or getattr(nodo, 'name', None)
            if not isinstance(nombre, str) or nombre.startswith('__'):
                continue
            assert nombre.isascii(), f"Identificador no ASCII '{nombre}' en {ruta.name}"
            partes = set(re.split(r'[_\d]+', nombre.lower()))
            conflictos = (partes & PALABRAS_INGLES_PROHIBIDAS) - EXCEPCIONES_E4_PERMITIDAS
            assert not conflictos, f'Términos en inglés {conflictos} en {ruta.name}:{nombre}'


def test_comentarios_y_textos_limpios():
    """Valida comentarios sobrios y textos de presentación sin marcas decorativas."""
    for ruta in RUTAS_AUDITADAS:
        if not ruta.exists():
            continue
        contenido = ruta.read_text(encoding='utf-8')
        fragmentos = _fragmentos_comentarios_y_textos(ruta, contenido)
        for fragmento, patrones in fragmentos:
            for patron in patrones:
                coincidencias = patron.findall(fragmento)
                assert not coincidencias, f'Patrón prohibido en {ruta.name}: {coincidencias}'


def _fragmentos_comentarios_y_textos(ruta, contenido):
    if ruta.suffix != '.py':
        return [(contenido, PATRONES_COMENTARIOS_PROHIBIDOS)]
    fragmentos = [(texto, PATRONES_COMENTARIOS_PROHIBIDOS)
                  for texto in comentarios_y_documentacion(contenido)]
    arbol = ast.parse(contenido)
    es_prueba = 'tests' in ruta.relative_to(RAIZ).parts
    fragmentos.extend((texto, PATRONES_COMENTARIOS_PROHIBIDOS[-2:])
                      for texto in cadenas_presentacion(arbol, es_prueba))
    return fragmentos


def test_reglas_css():
    """Valida reglas de movimiento, tokens de color y ausencia de vh en hojas CSS."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != '.css' or not ruta.exists():
            continue
        css = ruta.read_text(encoding='utf-8')
        assert not re.search(r'\b\d+vh\b', css), f"Uso de 'vh' prohibido en {ruta.name}"
        assert not re.search(r'transition:\s*all\b', css), f'transition: all en {ruta.name}'
        assert not re.search(r'ease-in\b', css), f'ease-in prohibido en {ruta.name}'
        duraciones = [int(m) for m in re.findall(r'(\d+)ms', css)]
        assert all(d <= 250 for d in duraciones), f'Duración > 250ms en {ruta.name}'


def test_reglas_python_frontend():
    """Valida ausencia de estilos en línea y cadenas extensas embebidas en Python."""
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != '.py' or not ruta.exists():
            continue
        arbol = ast.parse(ruta.read_text(encoding='utf-8'), filename=str(ruta))
        es_prueba = 'tests' in ruta.relative_to(RAIZ).parts
        for valor in cadenas_presentacion(arbol, es_prueba):
            assert 'style="' not in valor and "style='" not in valor, (
                f'Estilos en línea detectados en {ruta.name}'
            )
            if any(etiqueta in valor for etiqueta in ('<div', '<span', '<table', '<button')):
                lineas = valor.strip().splitlines()
                assert len(lineas) <= 3, (
                    f'HTML embebido de {len(lineas)} líneas (> 3) en {ruta.name}'
                )
