"""Cotejo estricto de predicados con propuestas nominales visibles para revisión."""
import ast
from collections import Counter

from tests.comun_conciliacion_ast import firma_ast


def predicado_control(nodo):
    """Separa el predicado del mensaje diagnóstico, que se registra por separado."""
    return nodo.test if isinstance(nodo, ast.Assert) else nodo


def forma_control(nodo):
    """Describe la forma para localizar candidatos; no acredita equivalencia."""
    return _forma(predicado_control(nodo))


def _forma(valor):
    if isinstance(valor, ast.AST):
        return (type(valor).__name__, tuple((campo, _forma(hijo))
                for campo, hijo in ast.iter_fields(valor)
                if campo not in {'id', 'attr', 'arg', 'kind'}
                and not (isinstance(valor, ast.Constant) and campo == 'value')))
    if isinstance(valor, list):
        return tuple(_forma(hijo) for hijo in valor)
    return valor


def proponer_equivalencias(antes, despues):
    """Propone traducciones conservando tipos; devuelve conflictos y cambios de constantes."""
    nombres = {}
    literales = {}
    conflictos = []
    _comparar_campos(predicado_control(antes), predicado_control(despues),
                     (nombres, literales, conflictos))
    return nombres, literales, conflictos


def _comparar_campos(antes, despues, registros):
    nombres, literales, conflictos = registros
    if type(antes) is not type(despues):
        conflictos.append(('tipo', type(antes).__name__, type(despues).__name__))
        return
    if isinstance(antes, ast.AST):
        _comparar_nodos(antes, despues, registros)
    elif isinstance(antes, list):
        if len(antes) != len(despues):
            conflictos.append(('longitud', len(antes), len(despues)))
        for origen, destino in zip(antes, despues):
            _comparar_campos(origen, destino, registros)
    elif antes != despues:
        conflictos.append(('valor', antes, despues))


def _comparar_nodos(antes, despues, registros):
    nombres, literales, conflictos = registros
    for campo, origen in ast.iter_fields(antes):
        destino = getattr(despues, campo)
        if campo in {'id', 'attr', 'arg'} and isinstance(origen, str):
            _registrar_nombre(type(antes).__name__ + ':' + origen, destino, nombres, conflictos)
        elif isinstance(antes, ast.Constant) and campo == 'value':
            if origen != destino:
                literales[(type(origen).__name__, repr(origen))] = destino
        else:
            _comparar_campos(origen, destino, registros)


def _registrar_nombre(origen, destino, nombres, conflictos):
    categoria = origen.split(':', 1)[0]
    colisiones = [nombre for nombre, valor in nombres.items()
                  if nombre != origen and nombre.startswith(categoria + ':') and valor == destino]
    if colisiones:
        conflictos.append(('colision', origen, colisiones, destino))
    if origen in nombres and nombres[origen] != destino:
        conflictos.append(('relacion', origen, nombres[origen], destino))
    nombres[origen] = destino


def comprobar_multiconjunto(controles, nombres, literales):
    """Conserva multiplicidad, constantes y operadores después del mapa explícito."""
    return Counter(firma_ast(predicado_control(control), nombres, literales)
                   for control in controles)
