"""Clasificacion exacta de una matriz aumentada reducida."""
from src.backend.constantes import SIN_SOLUCION, SOLUCION_UNICA, SOLUCIONES_INFINITAS
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.aritmetica import es_cero


def clasificar_sistema(matriz: Matriz, numero_variables: int, rango: int, tolerancia: float) -> tuple[str, str]:
    """Devuelve estado y mensaje segun matriz, columnas activas, rango y tolerancia flotante."""
    for fila in matriz.datos:
        todos_ceros = all(es_cero(valor, tolerancia) for valor in fila[:numero_variables])
        if todos_ceros and not es_cero(fila[numero_variables], tolerancia):
            return SIN_SOLUCION, "Sistema Inconsistente: Sin Solución."
    if rango < numero_variables:
        return SOLUCIONES_INFINITAS, "Sistema Consistente Indeterminado: Presenta Infinitas Soluciones"
    return SOLUCION_UNICA, "Sistema Consistente Determinado: Presenta Solución Única."
