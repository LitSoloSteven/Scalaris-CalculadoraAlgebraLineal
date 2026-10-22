"""Rastreo estático de controles extraídos a auxiliares de la suite, sin ejecutarlos."""
import ast
import copy
from dataclasses import dataclass

from tests.comun_conciliacion_ast import es_asercion


@dataclass
class ModuloPruebas:
    """Conserva el árbol, sus funciones locales y las importaciones propias resueltas."""
    ruta: str
    arbol: ast.Module
    funciones: dict
    importaciones: dict


@dataclass
class EstadoRecorrido:
    """Conserva la pila, los argumentos ligados y el alcance de la invocación."""
    pila: tuple
    enlaces: dict
    guardas: tuple
    modulo_argumentos: ModuloPruebas | None = None


def indexar_modulos(fuentes):
    """Resuelve únicamente módulos presentes en las fuentes, sin importar producción."""
    modulos = {}
    for ruta, texto in fuentes.items():
        if not ruta.endswith('.py'):
            continue
        arbol = ast.parse(texto)
        funciones = {nodo.name: nodo for nodo in arbol.body
                     if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef))}
        importaciones = _importaciones_propias(arbol, fuentes)
        modulos[ruta] = ModuloPruebas(ruta, arbol, funciones, importaciones)
    return modulos


def _importaciones_propias(arbol, fuentes):
    importaciones = {}
    for nodo in arbol.body:
        if not isinstance(nodo, ast.ImportFrom) or not nodo.module:
            continue
        destino = nodo.module.replace('.', '/') + '.py'
        if destino in fuentes:
            importaciones.update({nombre.asname or nombre.name: (destino, nombre.name)
                                  for nombre in nodo.names})
    return importaciones


def controles_efectivos(caso, ruta, modulos):
    """Incluye cada invocación explícita de un auxiliar y conserva la ruta de llamadas."""
    return _rastrear(caso, modulos[ruta], modulos, EstadoRecorrido((), {}, ()))


def _rastrear(funcion, modulo, modulos, estado):
    pila, enlaces, guardas = estado.pila, estado.enlaces, estado.guardas
    identidad = (modulo.ruta, funcion.name)
    if identidad in pila:
        return _resolver_ciclo(funcion, pila, identidad)
    recorrido = (*pila, identidad)
    controles = []
    locales = _funciones_locales(funcion)
    padres = {hijo: nodo for nodo in ast.walk(funcion) for hijo in ast.iter_child_nodes(nodo)}
    for nodo in _nodos_cuerpo(funcion):
        alcance = (*guardas, *_guardas_ancestros(nodo, padres))
        if es_asercion(nodo):
            controles.append({'ruta': modulo.ruta, 'linea': nodo.lineno,
                              'nodo': _enlazar(nodo, enlaces), 'recorrido': recorrido, 'alcance': alcance})
        elif isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            destino = _resolver_llamada(nodo, modulo, modulos, estado, locales)
            if destino:
                siguiente, definicion = destino
                parametros = _enlaces_llamada(definicion, nodo, enlaces)
                siguiente_estado = EstadoRecorrido(recorrido, parametros, alcance, modulo)
                controles.extend(_rastrear(definicion, siguiente, modulos, siguiente_estado))
    return controles


def _funciones_locales(funcion):
    return {nodo.name: nodo for nodo in ast.walk(funcion)
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _guardas_ancestros(nodo, padres):
    guardas = []
    actual = nodo
    while actual in padres:
        padre = padres[actual]
        guarda = _guarda_rama(padre, actual)
        if guarda:
            guardas.append(guarda)
        actual = padre
    return tuple(reversed(guardas))


def _guarda_rama(padre, hijo):
    if isinstance(padre, (ast.If, ast.While)):
        rama = 'alternativa' if hijo in padre.orelse else 'cuerpo'
        return {'tipo': type(padre).__name__, 'rama': rama, 'expresion': ast.unparse(padre.test)}
    if isinstance(padre, (ast.For, ast.AsyncFor)):
        return {'tipo': type(padre).__name__, 'expresion': ast.unparse(padre.iter),
                'objetivo': ast.unparse(padre.target), 'rama': 'alternativa' if hijo in padre.orelse else 'cuerpo'}
    if isinstance(padre, ast.ExceptHandler):
        return {'tipo': 'ExceptHandler', 'excepcion': ast.unparse(padre.type) if padre.type else None,
                'nombre': padre.name}
    if isinstance(padre, (ast.Try, ast.TryStar)):
        return _guarda_excepciones(padre, hijo)
    if isinstance(padre, (ast.With, ast.AsyncWith)):
        return {'tipo': type(padre).__name__, 'gestores': [ast.unparse(gestor) for gestor in padre.items]}
    return None


def _guarda_excepciones(padre, hijo):
    ramas = {'cuerpo': padre.body, 'alternativa': padre.orelse,
             'finalizacion': padre.finalbody, 'manejadores': padre.handlers}
    rama = next(nombre for nombre, sentencias in ramas.items() if hijo in sentencias)
    return {'tipo': type(padre).__name__, 'rama': rama,
            'excepciones': [ast.unparse(manejador.type) if manejador.type else None
                           for manejador in padre.handlers]}


def _resolver_ciclo(funcion, pila, identidad):
    if any(es_asercion(nodo) for nodo in ast.walk(funcion)):
        raise ValueError(f'Ciclo con controles de pruebas: {pila} -> {identidad}')
    return []


def _nodos_cuerpo(funcion):
    for sentencia in funcion.body:
        if isinstance(sentencia, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield from ast.walk(sentencia)


def _resolver_auxiliar(nombre, modulo, modulos, locales):
    if nombre in locales:
        return modulo, locales[nombre]
    if nombre in modulo.funciones:
        return modulo, modulo.funciones[nombre]
    if nombre in modulo.importaciones:
        ruta, simbolo = modulo.importaciones[nombre]
        destino = modulos[ruta]
        if simbolo in destino.funciones:
            return destino, destino.funciones[simbolo]
    return None


def _resolver_llamada(nodo, modulo, modulos, estado, locales):
    argumento = estado.enlaces.get(nodo.func.id)
    if isinstance(argumento, ast.Name) and estado.modulo_argumentos:
        return _resolver_auxiliar(argumento.id, estado.modulo_argumentos, modulos, {})
    return _resolver_auxiliar(nodo.func.id, modulo, modulos, locales)


def _enlaces_llamada(definicion, llamada, enlaces):
    argumentos = [*definicion.args.posonlyargs, *definicion.args.args]
    parametros = {parametro.arg: _enlazar(valor, enlaces)
                  for parametro, valor in zip(reversed(argumentos), reversed(definicion.args.defaults))}
    parametros.update({parametro.arg: _enlazar(valor, enlaces)
                       for parametro, valor in zip(argumentos, llamada.args)})
    parametros.update({parametro.arg: _enlazar(valor, enlaces)
                       for parametro, valor in zip(definicion.args.kwonlyargs, definicion.args.kw_defaults)
                       if valor is not None})
    parametros.update({opcion.arg: _enlazar(opcion.value, enlaces)
                       for opcion in llamada.keywords if opcion.arg})
    return parametros


class EnlazadorArgumentos(ast.NodeTransformer):
    """Sustituye referencias a parámetros por los argumentos de la invocación concreta."""

    def __init__(self, enlaces):
        self.enlaces = enlaces

    def visit_Name(self, nodo):
        """Conserva el resto de nombres y copia cada argumento para evitar mutaciones."""
        if isinstance(nodo.ctx, ast.Load) and nodo.id in self.enlaces:
            return copy.deepcopy(self.enlaces[nodo.id])
        return nodo


def _enlazar(nodo, enlaces):
    return EnlazadorArgumentos(enlaces).visit(copy.deepcopy(nodo))
