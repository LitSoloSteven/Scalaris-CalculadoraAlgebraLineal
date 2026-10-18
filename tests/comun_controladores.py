"""Preparación de cargas para controladores de sistemas lineales."""
import json


def procesar_sistema(controlador, carga):
    """Serializa una carga y decodifica la respuesta del controlador recibido."""
    return json.loads(controlador.procesar_sistema(json.dumps(carga)))
