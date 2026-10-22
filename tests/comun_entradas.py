"""Entradas compartidas con copia independiente para cada escenario de prueba."""
from copy import deepcopy
from fractions import Fraction

ENTRADAS_PRUEBA = {
    'sistema_unico': {
        'matriz_a': [['2', '1', '-1'], ['-3', '-1', '2'], ['-2', '1', '2']],
        'vector_b': ['8', '-11', '-3'], 'variables': ['x1', 'x2', 'x3'],
    },
    'independientes_incompletos': {
        'matriz_a': [['1', '0'], ['0', '1'], ['1', '1']],
        'vector_b': ['5'], 'variables': ['x1', 'x2'],
    },
    'filas_irregulares': {
        'matriz_a': [['1', '2'], ['3']],
        'vector_b': ['5', '6'], 'variables': ['x1', 'x2'],
    },
    'sistema_inconsistente': {
        'matriz_a': [['1', '1'], ['1', '1']],
        'vector_b': ['3', '5'], 'variables': ['x1', 'x2'],
    },
    'sistema_fraccionario': {
        'matriz_a': [['1', '2', '3'], ['3', '2', '1'], ['-1', '-2', '4']],
        'vector_b': ['0', '2', '2'], 'variables': None,
    },
    'sistema_paralelo': {
        'matriz_a': [['1', '2'], ['2', '4']],
        'vector_b': ['3', '7'], 'variables': ['x1', 'x2'],
    },
    'sistema_indeterminado': {
        'matriz_a': [['1', '2', '3'], ['2', '4', '6']],
        'vector_b': ['4', '8'], 'variables': ['x1', 'x2', 'x3'],
    },
    'vectores_plano': {
        'vectores': [{'datos': ['1', '2'], 'orientacion': 'columna'},
                     {'datos': ['3', '4'], 'orientacion': 'columna'}],
    },
    'combinacion_plano': {
        'objetivo': {'datos': ['5', '6'], 'orientacion': 'columna'},
        'vectores': [{'datos': ['1', '0'], 'orientacion': 'columna'},
                     {'datos': ['0', '1'], 'orientacion': 'columna'}],
    },
    'matrices_expresion': {
        'A': {'filas': 2, 'columnas': 2, 'datos': [['1', '2'], ['3', '4']]},
        'B': {'filas': 2, 'columnas': 2, 'datos': [['2', '0'], ['1', '3']]},
        'C': {'filas': 2, 'columnas': 2, 'datos': [['5', '1'], ['2', '4']]},
        'D': {'filas': 2, 'columnas': 2, 'datos': [['1', '-1'], ['0', '2']]},
    },
    'inversa_tres_por_tres': [
        [Fraction(-9, 2), Fraction(7), Fraction(-3, 2)],
        [Fraction(-2), Fraction(4), Fraction(-1)],
        [Fraction(3, 2), Fraction(-2), Fraction(1, 2)],
    ],
    'consumo_leontief': [[Fraction(1, 5), Fraction(3, 10)],
                         [Fraction(2, 5), Fraction(1, 10)]],
    'demanda_leontief': [Fraction(120), Fraction(80)],
    'captura_leontief': {
        'matriz_coeficientes': [['0.2', '0.3'], ['0.4', '0.1']],
        'vector_demanda': ['120', '80'],
    },
    'clasificacion_indeterminada': [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(3)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(6)],
        [Fraction(3), Fraction(3), Fraction(3), Fraction(9)],
    ],
    'clasificacion_incompatible': [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(5)],
        [Fraction(1), Fraction(2), Fraction(3), Fraction(4)],
    ],
    'rectas_incompatibles': {
        'matriz_a': [['1', '1'], ['1', '1']], 'vector_b': ['1', '2'],
    },
}


def copiar_entrada_prueba(nombre):
    """Devuelve una copia completa del caso solicitado; lanza KeyError si no existe."""
    return deepcopy(ENTRADAS_PRUEBA[nombre])
