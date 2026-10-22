"""Utilidades compartidas de serialización y parseo para controladores de interfaz."""
import json

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import formatear_fraccion_texto


def parsear_carga_json(
    carga_json: str,
    mensaje_esperado: str = "La carga debe ser un objeto JSON. Revisa los datos y vuelve a enviarlos.",
) -> tuple[dict | None, str | None]:
    """Devuelve el objeto JSON de la carga o un error serializado si su sintaxis o tipo falla."""
    try:
        datos = json.loads(carga_json)
    except json.JSONDecodeError as error:
        mensaje_error = (
            f"Carga JSON inválida: JSON malformado (línea {error.lineno}, columna {error.colno}). "
            "Revisa las comillas y los separadores y vuelve a enviarlo."
        )
        return None, json.dumps({"estado": "ERROR", "mensaje": mensaje_error})

    if not isinstance(datos, dict):
        return None, json.dumps({"estado": "ERROR", "mensaje": mensaje_esperado})

    return datos, None


def extraer_datos_matriz(matriz: Matriz) -> list[list]:
    """Devuelve una copia de las filas y valores exactos de la matriz recibida."""
    return [[matriz.obtener(fila, columna) for columna in range(matriz.columnas)]
            for fila in range(matriz.filas)]


def serializar_matriz(matriz: Matriz) -> dict:
    """Serializa una matriz a un diccionario con filas, columnas y datos en cadena."""
    return {
        "filas": matriz.filas,
        "columnas": matriz.columnas,
        "datos": [[formatear_fraccion_texto(valor) for valor in fila]
                  for fila in extraer_datos_matriz(matriz)],
    }


def construir_vista_pasos(pasos: list[dict]) -> list[dict]:
    """Genera la estructura estandarizada de pasos para la vista del reproductor."""
    vista_pasos = []
    for paso in pasos:
        matriz = paso.get("matriz")
        matriz_serializada = serializar_matriz(matriz) if matriz is not None else None
        pivote = list(paso["pivote"]) if paso.get("pivote") is not None else None
        filas_intercambio = list(paso["filas_intercambiadas"]) if paso.get("filas_intercambiadas") is not None else None
        vista_pasos.append({
            "indice": paso["indice"],
            "tipo": paso["tipo"],
            "descripcion": paso["descripcion"],
            "explicacion": paso["explicacion"],
            "indice_grupo": paso["indice_grupo"],
            "pivote": pivote,
            "filas_cambiadas": list(paso.get("filas_cambiadas", [])),
            "filas_intercambiadas": filas_intercambio,
            "matriz": matriz_serializada,
        })
    return vista_pasos
