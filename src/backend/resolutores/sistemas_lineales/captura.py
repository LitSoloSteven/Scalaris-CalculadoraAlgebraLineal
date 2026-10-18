"""Validación de captura y construcción exacta de sistemas aumentados."""
from fractions import Fraction
import json

from src.backend.excepciones import ErrorDatosMatriz
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz
from src.backend.resolutores.operaciones_matrices.celdas_exactas import parsear_celda_exacta


def _validar_dimensiones_aumentada(
    matriz_a_cruda: list, vector_b_crudo: list
) -> tuple[int, int, str | None]:
    """Valida la consistencia de forma y dimensiones entre matriz y vector."""
    error_estructura = _validar_estructura_captura(matriz_a_cruda, vector_b_crudo)
    if error_estructura:
        return 0, 0, error_estructura
    numero_filas = len(matriz_a_cruda)
    if numero_filas == 0:
        return 0, 0, json.dumps({"estado": "ERROR", "mensaje": "La matriz A está vacía."})
    if not isinstance(matriz_a_cruda[0], list):
        return 0, 0, json.dumps({"estado": "ERROR", "mensaje": "La matriz A debe ser una lista de filas."})
    numero_columnas = len(matriz_a_cruda[0])
    if numero_columnas == 0:
        return 0, 0, json.dumps({"estado": "ERROR", "mensaje": "La matriz A no puede tener 0 columnas."})

    valido, mensaje = ValidadorMatriz.validar_datos_matriz(matriz_a_cruda, numero_filas, numero_columnas)
    if not valido:
        return 0, 0, json.dumps({"estado": "ERROR", "mensaje": mensaje})
    if len(vector_b_crudo) != numero_filas:
        mensaje_resultado = f"El vector b tiene {len(vector_b_crudo)} valores; se esperaban {numero_filas} (uno por fila de A)."
        return 0, 0, json.dumps({"estado": "ERROR", "mensaje": mensaje_resultado})
    return numero_filas, numero_columnas, None


def _validar_estructura_captura(matriz_a: list, vector_b: list) -> str | None:
    """Rechaza contenedores inválidos y dimensiones excesivas antes de recorrer celdas."""
    mensaje = None
    if not isinstance(matriz_a, list) or any(not isinstance(fila, list) for fila in matriz_a):
        mensaje = "La matriz A debe ser una lista de filas."
    elif not isinstance(vector_b, list):
        mensaje = "El vector b debe ser una lista de valores."
    elif len(matriz_a) > DIMENSION_MAXIMA_SISTEMAS or any(len(fila) > DIMENSION_MAXIMA_SISTEMAS for fila in matriz_a):
        mensaje = f"El sistema excede el limite permitido ({DIMENSION_MAXIMA_SISTEMAS}x{DIMENSION_MAXIMA_SISTEMAS})."
    return json.dumps({"estado": "ERROR", "mensaje": mensaje}) if mensaje else None


def _parsear_celdas_a_fracciones(
    matriz_a_cruda: list, vector_b_crudo: list
) -> tuple[list[list[Fraction]] | None, list[Fraction] | None, str | None]:
    """Convierte celdas de matriz y vector a fracciones exactas con coordenadas."""
    try:
        a_fracciones = [
            [parsear_celda_exacta(celda, f"Error en A[{i+1},{j+1}]", vacio_como_cero=True)
             for j, celda in enumerate(fila)]
            for i, fila in enumerate(matriz_a_cruda)
        ]
        b_fracciones = [parsear_celda_exacta(celda, f"Error en b[{i+1}]", vacio_como_cero=True)
                        for i, celda in enumerate(vector_b_crudo)]
    except ValueError as error:
        return None, None, json.dumps({"estado": "ERROR", "mensaje": str(error)})
    return a_fracciones, b_fracciones, None


def validar_y_construir_aumentada(
    datos: dict,
) -> tuple[Matriz | None, list[list[Fraction]] | None, list[Fraction] | None, int, int, str | None]:
    """Construye la matriz aumentada [A | b] de una carga válida o devuelve su error."""
    matriz_a_cruda = datos.get("matriz_a", [])
    vector_b_crudo = datos.get("vector_b", [])

    numero_filas, numero_columnas, error_dim = _validar_dimensiones_aumentada(matriz_a_cruda, vector_b_crudo)
    if error_dim is not None:
        return None, None, None, 0, 0, error_dim

    a_fracciones, b_fracciones, error_parse = _parsear_celdas_a_fracciones(matriz_a_cruda, vector_b_crudo)
    if error_parse is not None or a_fracciones is None or b_fracciones is None:
        return None, None, None, 0, 0, error_parse

    try:
        datos_aumentados = [a_fracciones[i] + [b_fracciones[i]] for i in range(numero_filas)]
        matriz = Matriz(numero_filas, numero_columnas + 1, datos_aumentados)
    except ErrorDatosMatriz as error:
        return None, None, None, 0, 0, json.dumps({"estado": "ERROR", "mensaje": f"Datos inválidos: {error}"})

    return matriz, a_fracciones, b_fracciones, numero_filas, numero_columnas, None
