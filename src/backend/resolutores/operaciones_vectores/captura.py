"""Construcción exacta de vectores a partir de celdas de entrada."""
from src.backend.constantes import LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz


def validar_carga_vectorial(datos: dict, operacion: str) -> None:
    """Valida el esquema de la operación; lanza ValueError para claves o tipos ajenos."""
    claves = {
        "suma_resta": {"operacion", "vector_1", "vector_2", "estricto"},
        "escalar": {"escalar", "vector"},
        "combinacion_lineal": {"objetivo", "vectores"},
    }
    if set(datos) - claves[operacion]:
        raise ValueError("La carga contiene claves ajenas al contrato vectorial.")
    if operacion == "suma_resta":
        _validar_opciones_binarias(datos)
    if operacion == "combinacion_lineal" and not isinstance(datos.get("vectores"), list):
        raise ValueError("Los vectores deben ser una lista.")


def _validar_opciones_binarias(datos: dict) -> None:
    if datos.get("operacion") not in ("suma", "resta"):
        raise ValueError("La operacion debe ser suma o resta.")
    if not isinstance(datos.get("estricto", False), bool):
        raise ValueError("El modo estricto debe ser booleano.")


def parsear_escalar_capturado(escalar: object) -> object:
    """Convierte el escalar exacto; lanza ValueError con el diagnóstico de captura."""
    exito, valor, mensaje = ValidadorMatriz.parsear_numero_exacto(str(escalar))
    if not exito:
        raise ValueError(f"Escalar inválido: {mensaje}")
    return valor


def construir_vector_desde_diccionario(vector: dict) -> Matriz:
    """Construye una matriz fila o columna; lanza ValueError si una celda es inválida."""
    _validar_estructura_vector(vector)
    orientacion = vector.get("orientacion", "columna")
    valores = []
    for celda in vector.get("datos", []):
        texto = str(celda)
        exito, valor, mensaje = ValidadorMatriz.parsear_numero_exacto(texto)
        if not exito:
            if len(texto) > LONGITUD_MAXIMA_CADENA_NUMERO:
                raise ValueError(mensaje)
            raise ValueError(f"Valor inválido: {celda}. {mensaje}")
        valores.append(valor)
    if orientacion == "columna":
        return Matriz(len(valores), 1, [[valor] for valor in valores])
    return Matriz(1, len(valores), [valores])


def _validar_estructura_vector(vector: dict) -> None:
    """Exige datos canónicos y orientación válida, con columna como valor predeterminado."""
    if not isinstance(vector, dict) or set(vector) - {"orientacion", "datos"}:
        raise ValueError("El vector debe ser un objeto con datos y orientacion.")
    if vector.get("orientacion", "columna") not in ("columna", "fila"):
        raise ValueError("La orientacion debe ser columna o fila.")
    if not isinstance(vector.get("datos"), list) or not vector["datos"]:
        raise ValueError("Los datos del vector deben ser una lista no vacía.")
