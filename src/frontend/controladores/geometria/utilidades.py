"""Selectores de interfaz correspondientes a errores geométricos serializados."""


def selector_celda_error(celda_error: dict, *, escena: str = "", n_cuadricula: int = 0) -> str | None:
    """Devuelve el selector de una celda inválida para la escena y número de columnas."""
    if not celda_error:
        return None
    tipo = celda_error.get("tipo")
    if tipo == "A":
        fila, columna = celda_error.get("fila", 0), celda_error.get("columna", 0)
        return f'input[data-ecuaciones-fila="{fila}"][data-ecuaciones-columna="{columna}"]'
    if tipo == "b":
        fila = celda_error.get("fila", 0)
        return f'input[data-ecuaciones-fila="{fila}"][data-ecuaciones-columna="{n_cuadricula}"]'
    if tipo == "vector":
        nombre, indice = celda_error.get("nombre", ""), celda_error.get("indice", 0)
        panel = "geometria_vectores" if escena == "vectores" else "geometria_combinacion"
        return f'input[data-geometria-vector="{panel}_{nombre}"][data-geometria-indice="{indice}"]'
    return None
