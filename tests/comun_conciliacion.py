"""Inventario comparativo de casos, controles, preparación y parametrización de pruebas."""
import ast

from tests.comun_conciliacion_ast import funciones_prueba, preparacion_caso, firma_ast
from tests.comun_conciliacion_flujo import indexar_modulos, controles_efectivos
from tests.comun_conciliacion_informe import emparejar_controles


def conciliar_fuentes(anteriores, actuales, mapa, nominal):
    """Devuelve todos los controles y contextos, incluidos los pares que requieren revisión."""
    casos_antes = funciones_prueba(anteriores)
    casos_actuales = funciones_prueba(actuales)
    _validar_cobertura(casos_antes, mapa)
    modulos_antes = indexar_modulos(anteriores)
    modulos_actuales = indexar_modulos(actuales)
    resultados = []
    for entrada in mapa:
        origen = tuple(entrada['origen'])
        sucesores = [tuple(destino) for destino in entrada['sucesores']]
        anterior = _controles(casos_antes[origen], origen, modulos_antes)
        actuales_caso = []
        for destino in sucesores:
            actuales_caso.extend(_controles(casos_actuales[destino], destino, modulos_actuales))
        controles = emparejar_controles(anterior, actuales_caso, nominal)
        resultados.append({'origen': origen, 'sucesores': sucesores, 'controles': controles,
                           'preparacion_anterior': contexto_preparacion(casos_antes[origen], modulos_antes[origen[0]], modulos_antes),
                           'preparacion_actual': [contexto_preparacion(casos_actuales[d], modulos_actuales[d[0]], modulos_actuales)
                                                  for d in sucesores]})
    return resultados


def _validar_cobertura(casos, mapa):
    origenes = [tuple(entrada['origen']) for entrada in mapa]
    if set(casos) != set(origenes) or len(origenes) != len(set(origenes)):
        raise ValueError('El mapa debe cubrir cada función original exactamente una vez')


def _controles(caso, identidad, modulos):
    return controles_efectivos(caso, identidad[0], modulos)


def contexto_preparacion(caso, modulo, modulos):
    """Conserva el cuerpo, decoradores y dependencias de preparación sin ejecutarlos."""
    cuerpo = preparacion_caso(caso)
    llamadas = sorted({ast.unparse(nodo.func) for nodo in ast.walk(cuerpo)
                        if isinstance(nodo, ast.Call)})
    funciones = {nombre: ast.unparse(modulo.funciones[nombre])
                 for nombre in llamadas if nombre in modulo.funciones}
    return {'cuerpo': ast.unparse(cuerpo), 'firma_ast': firma_ast(cuerpo),
            'decoradores': [ast.unparse(nodo) for nodo in caso.decorator_list],
            'clases': _clases_caso(caso, modulo), 'preparaciones_modulo': _preparaciones_modulo(modulo),
            'modulos_preparacion': _modulos_preparacion(modulo, modulos),
            'auxiliares_locales': funciones, 'importaciones_propias': modulo.importaciones,
            'datos_modulo': [ast.unparse(nodo) for nodo in modulo.arbol.body
                             if isinstance(nodo, (ast.Assign, ast.AnnAssign))]}


def _clases_caso(caso, modulo):
    clases = []
    for nodo in modulo.arbol.body:
        if isinstance(nodo, ast.ClassDef) and _contiene_funcion(nodo, caso):
            clases.append(nodo.name)
    return clases


def _contiene_funcion(clase, caso):
    return any(hijo.name == caso.name and hijo.lineno == caso.lineno
               for hijo in clase.body if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)))


def _preparaciones_modulo(modulo):
    preparaciones = []
    for nodo in ast.walk(modulo.arbol):
        if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any('fixture' in ast.unparse(decorador) for decorador in nodo.decorator_list):
            preparaciones.append(ast.unparse(nodo))
    return preparaciones


def _modulos_preparacion(modulo, modulos):
    pendientes = [modulo.ruta, *_rutas_conftest(modulo.ruta, modulos)]
    encontrados = {}
    while pendientes:
        ruta = pendientes.pop()
        if ruta in encontrados:
            continue
        actual = modulos[ruta]
        encontrados[ruta] = {'cuerpo': ast.unparse(actual.arbol), 'firma_ast': firma_ast(actual.arbol)}
        pendientes.extend(destino for destino, nombre in actual.importaciones.values())
    return encontrados


def _rutas_conftest(ruta, modulos):
    partes = ruta.split('/')[:-1]
    candidatas = ['/'.join([*partes[:indice], 'conftest.py']) for indice in range(len(partes) + 1)]
    return [ruta for ruta in candidatas if ruta in modulos]
