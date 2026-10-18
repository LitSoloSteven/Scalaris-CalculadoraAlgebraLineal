"""Detección de secuencias Python repetidas con sus ubicaciones originales."""
import ast
from collections import defaultdict

DECLARACIONES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)


def _clave_secuencia(partes):
    arbol = ast.Module(body=partes, type_ignores=[])
    nombres = {}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
            nombres.setdefault(nodo.id, ('local', len(nombres)))
    return _firma_normalizada(arbol, nombres)


def _firma_normalizada(valor, nombres):
    if isinstance(valor, ast.Name):
        return ('Name', nombres.get(valor.id, ('externo', valor.id)), type(valor.ctx).__name__)
    if isinstance(valor, ast.AST):
        return (type(valor).__name__, tuple((campo, _firma_normalizada(hijo, nombres))
                                           for campo, hijo in ast.iter_fields(valor)))
    if isinstance(valor, list):
        return tuple(_firma_normalizada(hijo, nombres) for hijo in valor)
    return (type(valor).__name__, valor)


def _es_documentacion(nodo):
    return isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant) and isinstance(nodo.value.value, str)


def _es_declaracion(nodo):
    return isinstance(nodo, DECLARACIONES) or (isinstance(nodo, ast.AnnAssign) and nodo.value is None)


def _secuencias_sentencias(arbol):
    for nodo in ast.walk(arbol):
        for _, valor in ast.iter_fields(nodo):
            if isinstance(valor, list) and valor and all(isinstance(hijo, ast.stmt) for hijo in valor):
                yield valor


def _bloques_secuencia(sentencias):
    for indice, inicio in enumerate(sentencias):
        if _es_declaracion(inicio) or _es_documentacion(inicio):
            continue
        for fin in range(indice + 1, len(sentencias) + 1):
            partes = sentencias[indice:fin]
            if _es_declaracion(partes[-1]):
                break
            if partes[-1].end_lineno - inicio.lineno + 1 >= 5:
                yield partes


def duplicaciones_python(fuentes: dict[str, str]) -> list[list[tuple[str, int, int]]]:
    """Devuelve bloques repetidos de cinco líneas, incluso con variables locales renombradas."""
    bloques = defaultdict(list)
    for ruta, contenido in fuentes.items():
        for secuencia in _secuencias_sentencias(ast.parse(contenido)):
            for partes in _bloques_secuencia(secuencia):
                ubicacion = (ruta, partes[0].lineno, partes[-1].end_lineno)
                bloques[_clave_secuencia(partes)].append(ubicacion)
    repetidos = [ubicaciones for ubicaciones in bloques.values() if len(ubicaciones) > 1]
    return _bloques_maximos(repetidos)


def _esta_contenido(ubicaciones, grupo):
    return all(any(ruta == otra and inicio <= primero and ultimo <= fin
                   for otra, inicio, fin in grupo)
               for ruta, primero, ultimo in ubicaciones)


def _bloques_maximos(repetidos):
    maximos = []
    for ubicaciones in sorted(repetidos, key=lambda grupo: grupo[0][2] - grupo[0][1], reverse=True):
        if not any(_esta_contenido(ubicaciones, grupo) for grupo in maximos):
            maximos.append(ubicaciones)
    return maximos
