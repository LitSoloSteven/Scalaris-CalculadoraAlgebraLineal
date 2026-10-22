"""Validación de la envoltura JSON y delegación de escenas al dominio."""
import json
from collections.abc import Callable

from src.backend.geometria.errores import respuesta_error
from src.frontend.controladores.utilidades import parsear_carga_json


def procesar_carga(carga_json: str, campos: set[str], preparar: Callable[[dict], dict]) -> dict:
    """Valida sintaxis y campos únicos de una carga y devuelve la escena del dominio."""
    datos, error = parsear_carga_json(carga_json)
    if error:
        return respuesta_error(json.loads(error).get("mensaje", ""))
    if set(datos) - campos:
        return respuesta_error("Los datos recibidos no son válidos.")
    return preparar(datos)
