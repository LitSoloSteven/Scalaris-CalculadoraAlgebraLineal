"""Emparejamiento de controles para informes de conservación de pruebas."""
import ast
from collections import Counter
from difflib import SequenceMatcher

from tests.comun_conciliacion_comparacion import (
    forma_control, predicado_control, proponer_equivalencias,
)
from tests.comun_conciliacion_ast import NormalizadorNominal
import copy


def emparejar_controles(anteriores, actuales, nominal):
    """Propone pares uno a uno, manteniendo visibles los controles sin candidato."""
    opciones = [(puntuar_control(antes['nodo'], despues['nodo'], nominal), -abs(i - j), i, j)
                for i, antes in enumerate(anteriores) for j, despues in enumerate(actuales)
                if forma_control(antes['nodo']) == forma_control(despues['nodo'])]
    pares, ocupados = {}, set()
    for puntuacion, distancia, indice, destino in sorted(opciones, reverse=True):
        if indice not in pares and destino not in ocupados:
            pares[indice] = destino
            ocupados.add(destino)
    return [_fila_control(control, actuales[pares[indice]] if indice in pares else None)
            for indice, control in enumerate(anteriores)]


def puntuar_control(antes, despues, nominal):
    """Usa literales y miembros solo como puntuación, sin declarar equivalencia."""
    anteriores = _valores_control(antes, nominal)
    actuales = _valores_control(despues, {})
    total = sum(anteriores.values()) + sum(actuales.values())
    valores = 2 * sum((anteriores & actuales).values()) / (total or 1)
    miembros_antes = [nominal.get(nodo.attr, nodo.attr) for nodo in ast.walk(antes)
                      if isinstance(nodo, ast.Attribute)]
    miembros_despues = [nodo.attr for nodo in ast.walk(despues)
                        if isinstance(nodo, ast.Attribute)]
    textos_antes = _textos_control(antes, nominal)
    textos_despues = _textos_control(despues, {})
    semejanza = SequenceMatcher(None, textos_antes, textos_despues).ratio()
    prioridad = 10 if _predicado_nominal_candidato(antes, despues, nominal) else 0
    return prioridad + valores + semejanza + SequenceMatcher(None, miembros_antes, miembros_despues).ratio() / 10


def _predicado_nominal_candidato(antes, despues, nominal):
    traducido = NormalizadorNominal(nominal, nominal).visit(copy.deepcopy(antes))
    nombres, literales, conflictos = proponer_equivalencias(traducido, despues)
    return not literales and not conflictos


def _textos_control(control, nominal):
    textos = []
    for nodo in ast.walk(predicado_control(control)):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            texto = nominal.get(nodo.value, nodo.value)
            textos.append(texto)
    return '|'.join(textos)


def _valores_control(control, nominal):
    valores = []
    for nodo in ast.walk(predicado_control(control)):
        if isinstance(nodo, ast.Constant):
            valor = nominal.get(nodo.value, nodo.value) if isinstance(nodo.value, str) else nodo.value
            valores.append((type(valor).__name__, repr(valor)))
    return Counter(valores)


def _fila_control(antes, despues):
    fila = {'origen': (antes['ruta'], antes['linea']), 'antes': ast.unparse(antes['nodo']),
            'alcance_anterior': antes.get('alcance', ())}
    if despues is None:
        return {**fila, 'despues': None, 'conflictos': ['sin candidato']}
    nombres, literales, conflictos = proponer_equivalencias(antes['nodo'], despues['nodo'])
    if antes.get('alcance', ()) != despues.get('alcance', ()):
        conflictos.append(('alcance_pendiente', antes.get('alcance', ()), despues.get('alcance', ())))
    return {**fila, 'destino': (despues['ruta'], despues['linea']),
            'alcance_actual': despues.get('alcance', ()),
            'despues': ast.unparse(despues['nodo']), 'nombres': nombres,
            'literales': [{'antes': clave, 'despues': valor} for clave, valor in literales.items()],
            'conflictos': conflictos}
