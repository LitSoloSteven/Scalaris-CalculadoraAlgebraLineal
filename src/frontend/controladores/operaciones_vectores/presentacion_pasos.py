"""Preparación de tablas de pasos vectoriales desde el contrato serializado."""
from src.backend.resolutores.operaciones_vectores.captura_resultados import reconstruir_matriz_resultado
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_aumentada


def construir_tabla_paso_vectorial(paso: dict, numero_variables: int, variables: list[str]) -> str:
    """Delega la reconstrucción exacta al backend y devuelve la tabla escapada del paso."""
    datos_matriz = paso.get("matriz", {})
    matriz = reconstruir_matriz_resultado(datos_matriz)
    return html_tabla_aumentada(matriz, numero_variables, opciones={
        "filas_cambiadas": tuple(paso.get("filas_cambiadas") or ()),
        "pivote": tuple(paso["pivote"]) if paso.get("pivote") is not None else None,
        "filas_intercambio": tuple(paso["filas_intercambiadas"]) if paso.get("filas_intercambiadas") is not None else (),
        "bloque_resultado": False,
        "etiquetas_izquierda": variables,
        "etiquetas_derecha": ["b"],
    })
