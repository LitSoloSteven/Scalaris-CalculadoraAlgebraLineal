"""Análisis sintáctico de límites, comentarios y contenido de presentación."""
import ast
import io
import tokenize


def calcular_anidamiento_y_complejidad(nodo):
    """Cuenta decisiones y bloques; las ramas elif comparten profundidad."""
    resumen = [0, 1]
    for hijo in ast.iter_child_nodes(nodo):
        _visitar_complejidad(hijo, 0, resumen)
    return tuple(resumen)


def _visitar_complejidad(nodo, profundidad, resumen, rama_elif=False):
    if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return
    bloques = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith)
    siguiente = profundidad + int(isinstance(nodo, bloques) and not rama_elif)
    resumen[0] = max(resumen[0], siguiente)
    decisiones = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp)
    if isinstance(nodo, decisiones):
        resumen[1] += 1
    elif isinstance(nodo, ast.BoolOp):
        resumen[1] += len(nodo.values) - 1
    elif isinstance(nodo, ast.comprehension):
        resumen[1] += 1 + len(nodo.ifs)
    for hijo in ast.iter_child_nodes(nodo):
        _visitar_complejidad(hijo, siguiente, resumen, _es_rama_elif(nodo, hijo))


def _es_rama_elif(nodo, hijo):
    return (isinstance(nodo, ast.If) and len(nodo.orelse) == 1
            and hijo is nodo.orelse[0] and isinstance(hijo, ast.If)
            and hijo.col_offset == nodo.col_offset)


def nombres_parametros(nodo):
    """Incluye parámetros ordinarios, exclusivos y variádicos de una firma."""
    argumentos = nodo.args
    parametros = argumentos.posonlyargs + argumentos.args + argumentos.kwonlyargs
    parametros += [argumento for argumento in (argumentos.vararg, argumentos.kwarg)
                   if argumento is not None]
    return [argumento.arg for argumento in parametros if argumento.arg not in ("self", "cls")]


def declaraciones_publicas(arbol):
    """Recorre funciones, clases y métodos públicos, incluidos los asíncronos."""
    declaraciones = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    return [nodo for nodo in ast.walk(arbol)
            if isinstance(nodo, declaraciones) and not nodo.name.startswith("_")]


def comentarios_y_documentacion(contenido):
    """Extrae comentarios reales y docstrings sin interpretar datos de prueba."""
    comentarios = [token.string for token in tokenize.generate_tokens(io.StringIO(contenido).readline)
                   if token.type == tokenize.COMMENT]
    arbol = ast.parse(contenido)
    declaraciones = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    documentacion = [ast.get_docstring(nodo) for nodo in ast.walk(arbol)
                    if isinstance(nodo, declaraciones) and ast.get_docstring(nodo)]
    return comentarios + documentacion


def cadenas_presentacion(arbol, es_prueba=False):
    """Distingue contenido de producción de expectativas y muestras de pruebas."""
    if not es_prueba:
        return _extraer_cadenas(arbol)
    cadenas = []
    metodos = {"html", "markdown", "label", "button", "notify", "tooltip"}
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call) or not isinstance(nodo.func, ast.Attribute):
            continue
        if nodo.func.attr in metodos:
            cadenas.extend(_cadenas_argumentos(nodo))
    return cadenas


def _extraer_cadenas(nodo):
    return [valor.value for valor in ast.walk(nodo)
            if isinstance(valor, ast.Constant) and isinstance(valor.value, str)]


def _cadenas_argumentos(nodo):
    argumentos = nodo.args + [opcion.value for opcion in nodo.keywords]
    return [cadena for argumento in argumentos for cadena in _extraer_cadenas(argumento)]
