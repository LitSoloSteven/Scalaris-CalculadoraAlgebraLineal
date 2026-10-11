"""Utilidades compartidas de serialización y parseo para controladores de interfaz."""
import json
from typing import Any

from src.backend.utilidades.formateadores import formatear_fraccion_str


def parsear_payload(
    payload_json: str,
    mensaje_esperado: str = "El payload debe ser un objeto JSON.",
) -> tuple[dict | None, str | None]:
    """Valida la sintaxis del string JSON y asegura que sea un diccionario."""
    try:
        datos = json.loads(payload_json)
    except json.JSONDecodeError as error:
        mensaje_error = (
            f"Payload JSON malformado: {error.msg} "
            f"(línea {error.lineno}, columna {error.colno})."
        )
        return None, json.dumps({"status": "ERROR", "message": mensaje_error})

    if not isinstance(datos, dict):
        return None, json.dumps({"status": "ERROR", "message": mensaje_esperado})

    return datos, None


def serializar_matriz(matriz: Any) -> dict:
    """Serializa una matriz a un diccionario con filas, columnas y datos en cadena."""
    columnas = getattr(matriz, "columnas", getattr(matriz, "cols", 0))
    filas = getattr(matriz, "filas", getattr(matriz, "rows", 0))

    datos_formateados = []
    for r in range(filas):
        fila = []
        for c in range(columnas):
            valor = matriz.obtener(r, c) if hasattr(matriz, "obtener") else matriz.get(r, c)
            fila.append(formatear_fraccion_str(valor))
        datos_formateados.append(fila)

    return {
        "rows": filas,
        "cols": columnas,
        "data": datos_formateados,
        "filas": filas,
        "columnas": columnas,
        "datos": datos_formateados,
    }


def construir_vista_pasos(pasos: list[dict]) -> list[dict]:
    """Genera la estructura estandarizada de pasos para la vista del reproductor."""
    vista_pasos = []
    for p in pasos:
        mat = p.get("matrix")
        matriz_serializada = serializar_matriz(mat) if mat is not None else None
        pivote = list(p["pivot"]) if p.get("pivot") is not None else None
        filas_intercambio = list(p["swap_rows"]) if p.get("swap_rows") is not None else None
        vista_pasos.append({
            "index": p["index"],
            "kind": p["kind"],
            "description": p["description"],
            "explanation": p["explanation"],
            "group_index": p["group_index"],
            "pivot": pivote,
            "rows_changed": list(p.get("rows_changed", [])),
            "swap_rows": filas_intercambio,
            "matrix": matriz_serializada,
        })
    return vista_pasos
