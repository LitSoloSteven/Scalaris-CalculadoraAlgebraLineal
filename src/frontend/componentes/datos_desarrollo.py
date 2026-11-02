"""Clasificación y agrupación de trazas sin repetir cálculos del dominio."""
import re

_CELDA_PRODUCTO = re.compile(r"^C_\{([1-9][0-9]*),([1-9][0-9]*)\}\s*=")


def es_traza_producto(traza: list[dict]) -> bool:
    """Reconoce apertura, celdas y conclusión exacta de un producto del backend."""
    return (
        len(traza) >= 3
        and str(traza[0].get("descripcion", "")).startswith("Propiedad por comprobar:")
        and str(traza[-1].get("descripcion", "")).startswith("Comprobacion exacta de ")
        and all(_CELDA_PRODUCTO.match(str(paso.get("detalle_latex", ""))) for paso in traza[1:-1])
    )


def agrupar_filas_producto(traza: list[dict]) -> dict[int, list[str]]:
    """Agrupa los detalles ya calculados por su número de fila; ignora otras formas."""
    filas: dict[int, list[str]] = {}
    if not es_traza_producto(traza):
        return filas
    for paso in traza[1:-1]:
        detalle = paso["detalle_latex"]
        fila = int(_CELDA_PRODUCTO.match(detalle)[1])
        filas.setdefault(fila, []).append(detalle)
    return filas
