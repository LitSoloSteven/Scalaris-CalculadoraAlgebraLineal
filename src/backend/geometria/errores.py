"""Estados de error serializables del visualizador geométrico."""


def respuesta_error(mensaje: str, celda: dict | None = None, codigo: str | None = None) -> dict:
    """Devuelve un error con mensaje, celda opcional y código de clasificación."""
    respuesta = {"estado": "ERROR", "mensaje": mensaje, "celda_error": celda}
    if codigo is not None:
        respuesta["codigo"] = codigo
    return respuesta
