"""Captura acotada y exacta de ecuaciones para resolución y sincronización."""
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS, MAXIMO_CARACTERES_ECUACIONES
from src.backend.utilidades.analizadores import AnalizadorSistema


def preparar_ecuaciones(lineas: list[str]) -> dict:
    """Devuelve coeficientes serializables o un error de captura, sin perder precisión."""
    if sum(len(linea) for linea in lineas) > MAXIMO_CARACTERES_ECUACIONES:
        return {"estado": "ERROR", "mensaje": f"Reduce el texto a {MAXIMO_CARACTERES_ECUACIONES} caracteres."}
    if contar_ecuaciones(lineas) > DIMENSION_MAXIMA_SISTEMAS:
        return _error_dimension()
    correcto, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema("\n".join(lineas))
    if not correcto:
        return {"estado": "ERROR", "mensaje": mensaje}
    if len(variables) > DIMENSION_MAXIMA_SISTEMAS or matriz.filas > DIMENSION_MAXIMA_SISTEMAS:
        return _error_dimension()
    return {
        "estado": "EXITO", "mensaje": "",
        "matriz_a": [[str(valor) for valor in fila[:-1]] for fila in matriz.datos],
        "vector_b": [str(fila[-1]) for fila in matriz.datos],
        "variables": variables,
    }


def _error_dimension() -> dict:
    """Conserva el aviso de dimensión de la cuadrícula de sistemas."""
    return {"estado": "ERROR", "mensaje": f"El sistema excede el limite permitido ({DIMENSION_MAXIMA_SISTEMAS}x{DIMENSION_MAXIMA_SISTEMAS})."}


def contar_ecuaciones(lineas: list[str]) -> int:
    """Cuenta las ecuaciones escritas sin alterar las líneas originales."""
    return sum(bool(linea.strip()) for linea in "\n".join(lineas).splitlines())
