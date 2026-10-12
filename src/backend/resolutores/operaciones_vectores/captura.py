"""Construcción exacta de vectores a partir de celdas de entrada."""
from src.backend.constantes import LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz


def construir_vector_desde_dict(vector: dict) -> Matriz:
    """Construye una matriz fila o columna; lanza ValueError si una celda es inválida."""
    orientacion = vector.get("orientation", "column")
    valores = []
    for celda in vector.get("data", []):
        texto = str(celda)
        exito, valor, mensaje = ValidadorMatriz.parsear_numero_exacto(texto)
        if not exito:
            if len(texto) > LONGITUD_MAXIMA_CADENA_NUMERO:
                raise ValueError(mensaje)
            raise ValueError(f"Valor inválido: {celda}. {mensaje}")
        valores.append(valor)
    if orientacion == "column":
        return Matriz(len(valores), 1, [[valor] for valor in valores])
    return Matriz(1, len(valores), [valores])
