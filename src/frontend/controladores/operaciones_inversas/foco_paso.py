"""Cálculo de foco visual (filas antes/después y columnas) para un paso del reproductor."""

from src.frontend.controladores.utilidades import extraer_datos_matriz
from src.ai.contexto import extraer_filas
from src.frontend.controladores.clasificador_pasos import clasificar_paso


def _determinar_columna_central(pasos: list[dict], indice: int, analisis_paso: dict) -> int:
    """Identifica la columna sobre la cual recae el pivote o la operación del paso."""
    paso = pasos[indice]
    if paso.get("pivote"):
        return paso["pivote"][1]
    if analisis_paso.get("columna") is not None:
        return analisis_paso["columna"]
    for k in range(indice, -1, -1):
        if pasos[k].get("pivote"):
            return pasos[k]["pivote"][1]
    return 0


def _determinar_indices_foco(tipo_paso: str, analisis_paso: dict, paso: dict) -> tuple[list[int], list[int]]:
    """Calcula las listas de índices antes y después de la operación elemental."""
    r1, r2 = analisis_paso.get("fila_origen"), analisis_paso.get("fila_destino")
    if tipo_paso == "intercambio":
        return _foco_intercambio(r1, r2, paso)
    if tipo_paso == "eliminacion":
        destino = [r1] if r1 is not None else paso.get("filas_cambiadas", [0])
        origen = [r2] if (r2 is not None and r2 not in destino) else []
        return destino + origen, destino
    if tipo_paso in ("normalizacion", "pivote"):
        r = _fila_normalizada(r1, paso)
        return [r], [r]
    objetivo = list(paso.get("filas_cambiadas", [])) or ([paso["pivote"][0]] if paso.get("pivote") else [0])
    return objetivo, objetivo


def _foco_intercambio(r1, r2, paso):
    """Determina las dos filas intercambiadas cuando faltan índices analizados."""
    intercambio = paso.get("filas_intercambiadas") if (r1 is None or r2 is None) else None
    f1, f2 = (intercambio[0], intercambio[1]) if intercambio else (r1, r2)
    indices = [f1, f2] if f1 is not None and f2 is not None else []
    return indices, indices


def _fila_normalizada(fila, paso):
    """Prioriza la fila analizada, las filas cambiadas y el pivote, en ese orden."""
    if fila is not None:
        return fila
    cambio = paso.get("filas_cambiadas", [0])
    if cambio:
        return cambio[0]
    pivote = paso.get("pivote", [0])
    return pivote[0] if pivote else 0


def _extraer_foco_por_tipo(
    analisis_paso: dict,
    paso: dict,
    filas_previas: list,
    filas_actuales: list,
    columna_centro: int,
) -> tuple[dict, dict, list | None]:
    """Obtiene el extracto de filas afectadas según la clase de operación."""
    tipo_paso = analisis_paso.get("tipo", paso.get("tipo", "otro"))
    indice_antes, indice_despues = _determinar_indices_foco(tipo_paso, analisis_paso, paso)
    if not indice_antes and not indice_despues:
        return {}, {}, None
    antes, columnas_foco = extraer_filas(filas_previas, indice_antes, columna_centro)
    despues, _ = extraer_filas(filas_actuales, indice_despues, columna_centro)
    return antes, despues, columnas_foco


def construir_foco_paso(pasos: list[dict], indice: int) -> dict:
    """Calcula filas anteriores, posteriores y columnas que enfocan el paso."""
    if not pasos:
        return {"filas_antes": {}, "filas_despues": {}, "columnas": None}

    i = indice if (0 <= indice < len(pasos)) else (indice - 1 if 1 <= indice <= len(pasos) else max(0, min(indice, len(pasos) - 1)))
    paso = pasos[i]
    matriz = paso.get("matriz")
    if matriz is None:
        return {"filas_antes": {}, "filas_despues": {}, "columnas": None}

    filas = extraer_datos_matriz(matriz)
    matriz_anterior = pasos[i - 1].get("matriz", matriz) if i > 0 else matriz
    filas_anteriores = extraer_datos_matriz(matriz_anterior) if matriz_anterior else filas

    analisis_paso = clasificar_paso(paso.get("descripcion", ""))
    columna_centro = _determinar_columna_central(pasos, i, analisis_paso)

    antes, despues, columnas_foco = _extraer_foco_por_tipo(
        analisis_paso, paso, filas_anteriores, filas, columna_centro
    )
    return {"filas_antes": antes, "filas_despues": despues, "columnas": columnas_foco}
