"""Extractos acotados de las matrices y menores del paso seleccionado."""
from src.ai.contexto import describir_matriz, extraer_filas


def construir_meta_determinante(traza: list[dict], indice: int) -> dict:
    """Devuelve operación plana, filas antes/después y detalle del menor sin recalcular."""
    paso = traza[indice]
    matriz = paso.get("matriz")
    anterior = traza[indice - 1].get("matriz", matriz) if indice else matriz
    datos = paso.get("operacion", {})
    menor = paso.get("menor", {})
    fila = menor.get("fila", datos.get("fila", 0) + 1) - 1
    columna = menor.get("columna", datos.get("columna", 0) + 1) - 1
    filas = [fila]
    if paso["tipo"] == "intercambio":
        filas.append(datos["seleccionada"])
    elif paso["tipo"] == "eliminacion":
        filas.append(datos["fila_pivote"])
    antes, columnas = extraer_filas(anterior.datos if anterior else [], filas, columna)
    despues, _ = extraer_filas(matriz.datos if matriz else [], filas, columna)
    detalle = {"formula": paso.get("detalle_latex", ""), "explicacion": paso["explicacion"]}
    if menor:
        detalle.update(_detalle_menor(menor))
    return {"tipo": paso["tipo"], "operacion": paso["descripcion"],
            "filas_antes": antes, "filas_despues": despues, "columnas": columnas, "detalle": detalle}


def _detalle_menor(menor: dict) -> dict:
    campos = ("fila", "columna", "signo", "elemento", "valor_menor", "cofactor", "termino", "acumulado")
    detalle = {clave: str(menor[clave]) for clave in campos if clave in menor}
    detalle["filas_originales"] = list(menor.get("filas_originales", []))
    detalle["columnas_originales"] = list(menor.get("columnas_originales", []))
    if menor.get("matriz_menor") is not None:
        detalle["menor"] = describir_matriz(menor["matriz_menor"].datos)
    return detalle
