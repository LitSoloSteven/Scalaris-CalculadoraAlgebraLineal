"""Decisión de presentación para aplicar explícitamente una recomendación válida."""


def metodo_recomendado_disponible(respuesta: dict | None, metodo_actual: str) -> str | None:
    """Devuelve una recomendación distinta de la elegida; vacío o error devuelven None."""
    if not respuesta or respuesta.get('estado') != 'EXITO':
        return None
    metodo = respuesta.get('metodo_recomendado')
    return metodo if metodo in ('laplace', 'lu') and metodo != metodo_actual else None
