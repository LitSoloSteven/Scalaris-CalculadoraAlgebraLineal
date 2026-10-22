"""Vocabulario inglés de regresión para identificadores propios y documentación."""
import ast
import re

TERMINOS_INGLES = frozenset('''
    solver solvers matrix rows cols solve step steps controller view components models
    on change update show hide history fingerprint full kind legacy compat lhs rhs
    status stats match parsed payload params logger item items group swap setup method
    event callback data key dict list result text left right input output handler name
    width height size count target source start end evaluated comparison symbol symb
    coords fallback timeout debounce debounced chars config scripts badge display dock
    hub timer slider prompt flag backtick content client active interval default
    fmt idx val vals vars txt aug temp chip dev msj err
'''.split())

EXCEPCIONES_DECLARACIONES_E4 = {
    ('src/frontend/rutas.py', 'method'),
    ('src/frontend/rutas.py', 'handoff'),
    ('src/frontend/rutas.py', 'client'),
    ('src/frontend/controladores/operaciones_matrices/codificador.py', 'default'),
}
ATRIBUTOS_EXTERNOS_ESCRITOS = {
    'text': {'self.etiqueta_error', 'self.etiqueta_signo', 'self.etiqueta_bits', 'etiqueta'},
    'content': {"matriz['etiqueta_dimension_matriz']", "vector['etiqueta_dimension']",
                'self.etiqueta_forma', 'self.etiqueta_dimension_matriz'},
    'active': {'self.temporizador'},
    'interval': {'self.temporizador'},
    'value': {'entrada', 'celda', 'self.campo_entrada', 'vista.pestanas', 'self.pestanas_metodo',
              'self.entrada_a', 'self.entrada_b', 'self.deslizador'},
}


def palabras_identificador(nombre: str) -> set[str]:
    """Separa nombres ASCII con guiones bajos, dígitos y mayúsculas internas."""
    return {palabra.lower() for palabra in re.findall(r'[A-Z]+(?=[A-Z][a-z]|[^a-zA-Z]|$)|[A-Z]?[a-z]+', nombre)}


def declaraciones_propias(arbol):
    """Incluye variables locales, parámetros, atributos escritos y capturas de excepción."""
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Attribute) and ast.unparse(nodo.value) in ATRIBUTOS_EXTERNOS_ESCRITOS.get(nodo.attr, set()):
            continue
        nombre = _nombre_declarado(nodo)
        if nombre and not (nombre.startswith('__') and nombre.endswith('__')):
            yield nombre, nodo.lineno


def _nombre_declarado(nodo):
    if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
        return nodo.id
    if isinstance(nodo, ast.arg):
        return nodo.arg
    if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.ExceptHandler)):
        return nodo.name
    if isinstance(nodo, ast.Attribute) and isinstance(nodo.ctx, ast.Store):
        return nodo.attr
    return None


def ingles_propio(nombre, ruta):
    """Devuelve conflictos del vocabulario, salvo contratos impuestos en la ubicación exacta."""
    if (ruta, nombre) in EXCEPCIONES_DECLARACIONES_E4:
        return set()
    return palabras_identificador(nombre) & TERMINOS_INGLES
