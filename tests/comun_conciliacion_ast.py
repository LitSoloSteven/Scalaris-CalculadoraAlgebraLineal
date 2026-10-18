"""Huellas estructurales de pruebas que conservan valores y relaciones entre nombres."""
import ast
import copy
from collections import Counter


def funciones_prueba(fuentes):
    """Indexa casos por archivo y nombre cualificado, incluidas las clases de pytest."""
    casos = {}
    for ruta, texto in fuentes.items():
        if ruta.endswith('.py'):
            _recoger_funciones(ast.parse(texto), ruta, (), casos)
    return casos


def _recoger_funciones(nodo, ruta, padres, casos):
    for hijo in ast.iter_child_nodes(nodo):
        if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hijo.name.startswith('test_'):
                casos[(ruta, '.'.join((*padres, hijo.name)))] = hijo
        elif isinstance(hijo, ast.ClassDef):
            _recoger_funciones(hijo, ruta, (*padres, hijo.name), casos)
        else:
            _recoger_funciones(hijo, ruta, padres, casos)


class NormalizadorNominal(ast.NodeTransformer):
    """Aplica equivalencias explícitas sin borrar operadores, constantes ni receptores."""

    def __init__(self, nombres, literales=None):
        self.nombres = nombres
        self.literales = literales or {}

    def visit_Name(self, nodo):
        """Conserva la identidad de cada variable al traducir su nombre."""
        nodo.id = self.nombres.get('Name:' + nodo.id, self.nombres.get(nodo.id, nodo.id))
        return nodo

    def visit_Attribute(self, nodo):
        """Traduce el miembro y mantiene la expresión que identifica su receptor."""
        self.generic_visit(nodo)
        nodo.attr = self.nombres.get('Attribute:' + nodo.attr, self.nombres.get(nodo.attr, nodo.attr))
        return nodo

    def visit_keyword(self, nodo):
        """Traduce argumentos nombrados propios conservando sus valores."""
        self.generic_visit(nodo)
        if nodo.arg is not None:
            nodo.arg = self.nombres.get('keyword:' + nodo.arg, self.nombres.get(nodo.arg, nodo.arg))
        return nodo

    def visit_Constant(self, nodo):
        """Sustituye únicamente literales registrados de forma explícita."""
        if isinstance(nodo.value, str):
            nodo.value = self.literales.get(nodo.value, nodo.value)
        return nodo


def firma_ast(nodo, nombres=None, literales=None):
    """Devuelve una huella AST sin ubicaciones, con todas las constantes y operadores."""
    copia = NormalizadorNominal(nombres or {}, literales).visit(copy.deepcopy(nodo))
    return ast.dump(copia, include_attributes=False)


def aserciones_caso(caso):
    """Incluye assert, raises y llamadas de aserción de unittest o pytest."""
    return [nodo for nodo in ast.walk(caso) if es_asercion(nodo)]


def es_asercion(nodo):
    """Reconoce controles explícitos sin confundir llamadas de preparación."""
    if isinstance(nodo, ast.Assert):
        return True
    return (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
            and (nodo.func.attr == 'raises' or nodo.func.attr.startswith('assert')))


def multiconjunto_aserciones(caso, nombres=None, literales=None):
    """Cuenta también repeticiones; no convierte las aserciones en un conjunto."""
    return Counter(firma_ast(nodo, nombres, literales) for nodo in aserciones_caso(caso))


def preparacion_caso(caso):
    """Conserva asignaciones, llamadas, bucles y ramas al retirar documentación y controles."""
    copia = copy.deepcopy(caso)
    copia.decorator_list = []
    copia.body = _sin_controles(copia.body)
    copia.name = 'caso'
    return copia


def _sin_controles(sentencias):
    salida = []
    for sentencia in sentencias:
        if isinstance(sentencia, ast.Assert) or _es_documentacion(sentencia):
            continue
        for campo, valor in ast.iter_fields(sentencia):
            if isinstance(valor, list) and valor and isinstance(valor[0], ast.stmt):
                setattr(sentencia, campo, _sin_controles(valor))
        salida.append(sentencia)
    return salida


def _es_documentacion(nodo):
    return (isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant)
            and isinstance(nodo.value.value, str))
