"""Descriptores y extractos matriciales para el contexto pedagógico."""
from typing import Any, Sequence
from src.ai.constantes import (
    COLUMNAS_MAXIMAS_RECORTE, MAXIMO_MATRIZ_COMPLETA, TAMANIO_VENTANA_MATRIZ,
)
from src.ai.texto_contexto import compactar_numero
from src.ai.ventana_matriz import extraer_ventana_matriz


def _es_celda_invalida(valor: str) -> bool:
    if valor in ("0", "", "0.0"):
        return False
    try:
        float(valor.split("/")[0]) if "/" in valor else float(valor)
        return False
    except Exception:
        return True


def describir_matriz(
    filas: Sequence[Sequence[Any]], *, maximo_completa: int = MAXIMO_MATRIZ_COMPLETA,
    ventana: int = TAMANIO_VENTANA_MATRIZ,
) -> dict:
    """Describe dimensiones y datos visibles conservando el recuento de errores."""
    total_filas = len(filas)
    total_columnas = len(filas[0]) if total_filas > 0 else 0
    if total_filas <= maximo_completa and total_columnas <= maximo_completa:
        datos = [[compactar_numero(celda) for celda in fila] for fila in filas]
        return {"filas": total_filas, "columnas": total_columnas, "datos": datos}
    filas_visibles, columnas_visibles = min(total_filas, ventana), min(total_columnas, ventana)
    datos, invalidos = extraer_ventana_matriz(
        filas, total_columnas, (filas_visibles, columnas_visibles), compactar_numero, _es_celda_invalida,
    )
    resultado = {
        "filas": total_filas, "columnas": total_columnas,
        "ventana": [filas_visibles, columnas_visibles], "datos": datos,
    }
    if invalidos > 0:
        resultado["invalidos"] = invalidos
    return resultado


def generar_nota_ventana(*descriptores: dict) -> str | None:
    """Describe la ventana de la mayor matriz recortada o devuelve ausencia de nota."""
    con_ventana = [
        descriptor for descriptor in descriptores
        if isinstance(descriptor, dict) and isinstance(descriptor.get("ventana"), (list, tuple))
        and len(descriptor["ventana"]) >= 2
    ]
    if not con_ventana:
        return None
    mayor = max(con_ventana, key=lambda descriptor: descriptor.get("filas", 0) * descriptor.get("columnas", 0))
    filas_visibles, columnas_visibles = mayor["ventana"][0], mayor["ventana"][1]
    filas, columnas = mayor.get("filas", 0), mayor.get("columnas", 0)
    return f"ventana {filas_visibles}×{columnas_visibles} de {filas}×{columnas}"


def extraer_filas(
    filas_datos: Sequence[Sequence[Any]], indices_filas: Sequence[int], columna_centro: int,
    columnas_maximas: int = COLUMNAS_MAXIMAS_RECORTE,
) -> tuple[dict[str, list[str]], tuple[int, int] | None]:
    """Extrae filas y una ventana de columnas centrada alrededor del pivote."""
    total_columnas = len(filas_datos[0]) if filas_datos else 0
    inicio_columna, fin_columna, rango_columnas = 0, total_columnas, None
    if total_columnas > columnas_maximas:
        inicio_columna = max(0, columna_centro - columnas_maximas // 2)
        fin_columna = min(total_columnas, inicio_columna + columnas_maximas)
        if fin_columna - inicio_columna < columnas_maximas:
            inicio_columna = max(0, fin_columna - columnas_maximas)
        rango_columnas = (inicio_columna + 1, fin_columna)
    resultado = {}
    for indice in indices_filas:
        if 0 <= indice < len(filas_datos):
            fila = filas_datos[indice]
            resultado[str(indice + 1)] = [compactar_numero(celda) for celda in fila[inicio_columna:fin_columna]]
    return resultado, rango_columnas
