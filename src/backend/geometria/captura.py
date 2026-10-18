"""Validación exacta y localización de errores en entradas geométricas."""
from src.backend.geometria.errores import respuesta_error
from src.backend.utilidades.validadores import ValidadorMatriz


def ubicar_error_celda(matriz: list, vector: list) -> dict | None:
    """Devuelve la primera coordenada numérica inválida de una matriz y su término."""
    if not isinstance(matriz, list) or not isinstance(vector, list):
        return None
    for i, fila in enumerate(matriz):
        if not isinstance(fila, list):
            return None
        for j, celda in enumerate(fila):
            if not _celda_valida(celda):
                return {"tipo": "A", "fila": i, "columna": j}
    for i, celda in enumerate(vector):
        if not _celda_valida(celda):
            return {"tipo": "b", "fila": i}
    return None


def _celda_valida(celda) -> bool:
    texto = str(celda).strip() if celda is not None and str(celda).strip() else "0"
    return ValidadorMatriz.parsear_numero_exacto(texto)[0]


def ubicar_error_vector(nombre: str, datos: list) -> dict | None:
    """Devuelve el nombre e índice de la primera celda inválida de un vector."""
    if not isinstance(datos, list):
        return None
    for indice, celda in enumerate(datos):
        if not ValidadorMatriz.parsear_numero_exacto(str(celda).strip() or "0")[0]:
            return {"tipo": "vector", "nombre": nombre, "indice": indice}
    return None


def parsear_par_vectores(vectores: list) -> tuple[list | None, dict | None]:
    """Convierte dos entradas vectoriales en fracciones o devuelve su error granular."""
    nombres = ["u", "v"]
    resultado = []
    for indice, entrada in enumerate(vectores):
        datos = entrada if isinstance(entrada, list) else entrada.get("datos", []) if isinstance(entrada, dict) else None
        if not isinstance(datos, list):
            return None, respuesta_error("Datos de vector inválidos.")
        componentes, error = _parsear_componentes(datos, nombres[indice])
        if error:
            return None, error
        resultado.append(componentes)
    return resultado, None


def _parsear_componentes(datos: list, nombre: str) -> tuple[list | None, dict | None]:
    componentes = []
    for indice, celda in enumerate(datos):
        texto = str(celda).strip() if celda is not None else "0"
        valido, valor, mensaje = ValidadorMatriz.parsear_numero_exacto(texto or "0")
        if not valido:
            coordenada = {"tipo": "vector", "nombre": nombre, "indice": indice}
            return None, respuesta_error(f"Error en {nombre}[{indice + 1}]: {mensaje}", coordenada)
        componentes.append(valor)
    return componentes, None
