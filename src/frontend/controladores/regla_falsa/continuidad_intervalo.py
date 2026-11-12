"""Consulta geométrica de regla falsa independiente de la configuración de parada."""
import json

from src.backend.resolutores.raices.preparacion_regla_falsa import preparar_intervalo_regla_falsa
from .captura import preparar_entrada
from .serializacion import serializar_resultado

CLAVES_CONTINUIDAD = ("expresion", "extremo_izquierdo", "extremo_derecho", "unidad_angular")


def consultar_continuidad(captura: dict) -> dict:
    """Devuelve informe, extremos y fallos finitos sin exponer el evaluador ni ejecutar iteraciones."""
    try:
        datos = {clave: captura[clave] for clave in CLAVES_CONTINUIDAD if clave in captura}
        preparado = preparar_intervalo_regla_falsa(preparar_entrada(datos))
        respuesta = {
            "informe": preparado.informe,
            "evaluaciones": preparado.evaluaciones,
            "restriccion": preparado.restriccion,
            "fallo": serializar_resultado(preparado.fallo) if preparado.fallo is not None else None,
        }
        json.dumps(respuesta, allow_nan=False)
        return respuesta
    except ValueError as error:
        return {"mensaje": str(error)}
