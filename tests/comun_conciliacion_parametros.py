"""Lectura estática de parametrizaciones literales para contextualizar controles."""
import ast
import copy
from itertools import product

from tests.comun_conciliacion_flujo import EnlazadorArgumentos


def parametrizaciones_literales(caso):
    """Devuelve enlaces para tablas literales; rechaza fuentes calculadas o fixtures indirectas."""
    tablas = []
    for decorador in caso.decorator_list:
        if isinstance(decorador, ast.Call) and isinstance(decorador.func, ast.Attribute):
            if decorador.func.attr == 'parametrize':
                tablas.append(_tabla_parametros(decorador))
    if not tablas:
        return [{}]
    combinaciones = []
    for combinacion in product(*tablas):
        enlaces = {}
        for tabla in combinacion:
            enlaces.update(tabla)
        combinaciones.append(enlaces)
    return combinaciones


def _tabla_parametros(decorador):
    if len(decorador.args) < 2:
        raise ValueError('Parametrización sin nombres o valores explícitos')
    if any(opcion.arg == 'indirect' for opcion in decorador.keywords):
        raise ValueError('La parametrización indirecta requiere revisar sus fixtures')
    nombres = ast.literal_eval(decorador.args[0])
    nombres = nombres.split(',') if isinstance(nombres, str) else nombres
    nombres = [nombre.strip() for nombre in nombres]
    valores = decorador.args[1]
    if not isinstance(valores, (ast.List, ast.Tuple)):
        raise ValueError('La tabla de parámetros requiere resolver datos de módulo')
    return [_enlaces_fila(nombres, fila) for fila in valores.elts]


def _enlaces_fila(nombres, fila):
    if len(nombres) != 1 and not isinstance(fila, (ast.List, ast.Tuple)):
        raise ValueError('La fila de varios parámetros requiere una lista o tupla explícita')
    valores = [fila] if len(nombres) == 1 else fila.elts
    if len(valores) != len(nombres):
        raise ValueError('El número de valores no coincide con los parámetros')
    return dict(zip(nombres, valores))


def expandir_controles_parametrizados(controles, caso):
    """Conserva cada entrada literal y sus argumentos específicos en cada control."""
    salida = []
    for enlaces in parametrizaciones_literales(caso):
        for control in controles:
            copia = {**control, 'nodo': EnlazadorArgumentos(enlaces).visit(copy.deepcopy(control['nodo']))}
            copia['parametros'] = {nombre: ast.unparse(valor) for nombre, valor in enlaces.items()}
            salida.append(copia)
    return salida
