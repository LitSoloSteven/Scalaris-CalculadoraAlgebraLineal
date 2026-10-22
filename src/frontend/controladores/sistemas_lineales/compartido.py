"""Metadatos pedagógicos de pasos de sistemas lineales."""
from typing import Any
from src.frontend.controladores.utilidades import extraer_datos_matriz
from src.frontend.controladores.clasificador_pasos import clasificar_paso

def _determinar_filas_objetivo(
    tipo_paso: str, r1: int | None, r2: int | None
) -> tuple[list[int], list[int], int | None]:
    """Retorna las listas de índices de filas antes, después y fila del pivote."""
    if r1 is None:
        return [], [], None
    if tipo_paso == "intercambio" and r2 is not None:
        return [r1, r2], [r1, r2], r1
    if tipo_paso == "eliminacion" and r2 is not None:
        return [r1, r2], [r1], r2
    if tipo_paso == "normalizacion":
        return [r1], [r1], r1
    return [], [], None


def _extraer_detalles_paso(
    tipo_paso: str,
    analisis_paso: dict,
    columna_pivote_actual: int,
    filas_previas: list,
    filas_actuales: list,
) -> tuple[list[int] | None, dict, dict, list | None, int]:
    """Calcula pivote y extractos de filas antes y después según la operación."""
    from src.ai.contexto import extraer_filas

    r1, r2 = analisis_paso.get("fila_origen"), analisis_paso.get("fila_destino")
    if tipo_paso == "pivote" and r1 is not None and analisis_paso.get("columna") is not None:
        columna = analisis_paso["columna"]
        return [r1, columna], {}, {}, None, columna

    filas_anteriores, filas_desp, fila_pivote = _determinar_filas_objetivo(tipo_paso, r1, r2)
    if not filas_anteriores or fila_pivote is None:
        return None, {}, {}, None, columna_pivote_actual

    filas_antes, rango_columnas = extraer_filas(filas_previas, filas_anteriores, columna_pivote_actual)
    filas_despues, _ = extraer_filas(filas_actuales, filas_desp, columna_pivote_actual)
    return [fila_pivote, columna_pivote_actual], filas_antes, filas_despues, rango_columnas, columna_pivote_actual


def construir_metadatos_pasos(pasos_crudos: list[dict], matriz_inicial: Any = None) -> list[dict]:
    """Genera metadatos estructurados de pasos para renderizado y explicaciones."""
    meta = []
    total = len(pasos_crudos)
    columna_pivote_actual = 0

    for i, paso in enumerate(pasos_crudos):
        desc = paso.get("descripcion", "")
        matriz = paso.get("matriz")
        filas_actuales = extraer_datos_matriz(matriz) if matriz else []
        analisis_paso = clasificar_paso(desc)
        tipo_paso = analisis_paso["tipo"]

        if i > 0:
            matriz_previa = pasos_crudos[i - 1].get("matriz")
        else:
            matriz_previa = matriz_inicial if matriz_inicial is not None else matriz
        filas_previas = extraer_datos_matriz(matriz_previa) if matriz_previa else filas_actuales

        pivote, antes, despues, columnas_rango, columna_pivote_actual = _extraer_detalles_paso(
            tipo_paso, analisis_paso, columna_pivote_actual, filas_previas, filas_actuales
        )
        meta.append({
            "indice": i + 1,
            "total": total,
            "tipo": tipo_paso,
            "operacion": desc,
            "pivote": pivote,
            "filas_antes": antes,
            "filas_despues": despues,
            "columnas": list(columnas_rango) if columnas_rango else None,
        })
    return meta
