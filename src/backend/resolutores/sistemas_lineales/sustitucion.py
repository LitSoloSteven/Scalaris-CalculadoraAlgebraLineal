"""Adaptacion del calculo parametrico al contrato de resolucion de sistemas."""
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.calculo_solucion import calcular_solucion_parametrica
from src.backend.resolutores.sistemas_lineales.presentacion_sustitucion import presentar_sustitucion


def ejecutar_sustitucion_hacia_atras(matriz: Matriz, columnas_pivote: list[int],
                                   numero_variables: int, nombres_variables: list[str] | None) -> tuple:
    """Devuelve solucion, exacta opcional, pasos, libres y parametros de la matriz escalonada recibida."""
    parametros = calcular_solucion_parametrica(matriz, columnas_pivote, numero_variables)
    return presentar_sustitucion(parametros, columnas_pivote, nombres_variables)
