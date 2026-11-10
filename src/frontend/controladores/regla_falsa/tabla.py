"""Columnas y acciones de la traza real de regla falsa."""
from src.frontend.controladores.biseccion.presentacion import numero

COLUMNAS = (
    ("i", "i"), ("extremo_izquierdo", "a"), ("extremo_derecho", "b"),
    ("valor_izquierdo", "f(a)"), ("valor_derecho", "f(b)"), ("aproximacion", "c"),
    ("valor_aproximacion", "f(c)"), ("residuo", "|f(c)|"), ("ancho", "Ancho"),
    ("peso_secante", "Peso de secante"), ("error_relativo_porcentual", "Error relativo %"),
    ("signo_producto", "Signo f(a)·f(c)"), ("accion", "Acción"),
)
ACCIONES = {"reemplazar_a": "a = c", "reemplazar_b": "b = c",
            "raiz": "Cero evaluado", "sin_cambio": "Intervalo conservado"}


def filas_tabla(filas: tuple, completo: bool = False) -> list[dict]:
    """Formatea las filas recibidas sin alterar las métricas ni inferir acciones del motor."""
    return [{clave: valor_columna(fila, clave, completo) for clave, _ in COLUMNAS} for fila in filas]


def valor_columna(fila: dict, clave: str, completo: bool = False) -> str:
    """Devuelve una celda de texto; el error relativo nulo se presenta como no disponible."""
    if clave == "accion":
        return ACCIONES[fila[clave]]
    if clave == "signo_producto":
        return {-1: "Negativo", 0: "Cero", 1: "Positivo"}[fila[clave]]
    return numero(fila[clave], completo)
