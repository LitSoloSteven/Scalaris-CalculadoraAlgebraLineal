"""Conversión exacta de entradas de Leontief y transformaciones lineales."""
from fractions import Fraction
from src.backend.modelos.matriz import Matriz
from .celdas_exactas import parsear_celda_exacta


def parsear_matriz_modelo(datos_crudos: list, simbolo: str, cuadrada: bool = False) -> Matriz:
    """Convierte filas crudas en Matriz; señala con ValueError estructuras o celdas inválidas."""
    filas = len(datos_crudos)
    if filas == 0:
        raise ValueError(f"La matriz {simbolo} no puede estar vacía.")
    if not isinstance(datos_crudos[0], list):
        raise ValueError(f"Fila 1 de {simbolo} no es una lista.")
    columnas = filas if cuadrada else len(datos_crudos[0])
    datos_exactos = []
    for indice_fila, fila in enumerate(datos_crudos):
        if not isinstance(fila, list):
            raise ValueError(f"Fila {indice_fila+1} de {simbolo} no es una lista.")
        if len(fila) != columnas:
            raise ValueError(f"Fila {indice_fila+1} de {simbolo} tiene {len(fila)} columnas; se esperaban {columnas}.")
        datos_exactos.append(_parsear_fila(fila, simbolo, indice_fila))
    return Matriz(filas, columnas, datos_exactos)


def _parsear_fila(fila: list, simbolo: str, indice_fila: int) -> list[Fraction]:
    """Convierte una fila numérica conservando el mensaje con coordenadas matemáticas."""
    return [parsear_celda_exacta(celda, f"{simbolo}[{indice_fila+1},{indice_columna+1}]")
            for indice_columna, celda in enumerate(fila)]


def parsear_vector_demanda(datos_crudos: list) -> list[Fraction]:
    """Convierte demanda cruda en fracciones; lanza ValueError con el índice inválido."""
    return [parsear_celda_exacta(celda, f"d[{indice+1}]")
            for indice, celda in enumerate(datos_crudos)]


def validar_nombres(nombres: object, etiqueta: str) -> list[str] | None:
    """Acepta listas de nombres literales o ausencia; rechaza tipos ajenos con ValueError."""
    if not nombres:
        return None
    if not isinstance(nombres, list) or any(not isinstance(nombre, str) for nombre in nombres):
        raise ValueError(f"{etiqueta} debe ser una lista de textos.")
    return nombres
