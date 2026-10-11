"""Controlador de transformaciones lineales para la capa de presentación."""
import json
import logging

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.transformaciones import (
    ResolutorTransformacionesLineales,
)
from src.backend.utilidades.validadores import ValidadorMatriz

logger = logging.getLogger(__name__)


def _parsear_matriz_a(a_raw: list) -> Matriz:
    """Valida y convierte la matriz representante de la transformación a fracciones exactas."""
    m = len(a_raw)
    if m == 0:
        raise ValueError("La matriz A no puede estar vacía.")
    n = len(a_raw[0])
    datos_a = []
    for i, fila in enumerate(a_raw):
        if len(fila) != n:
            raise ValueError(
                f"Fila {i+1} de A tiene {len(fila)} columnas; se esperaban {n}."
            )
        fila_parseada = []
        for j, raw in enumerate(fila):
            texto = str(raw).strip() if raw is not None else "0"
            ok, val, err = ValidadorMatriz.parsear_numero_exacto(texto)
            if not ok:
                raise ValueError(f"A[{i+1},{j+1}]: {err}")
            fila_parseada.append(val)
        datos_a.append(fila_parseada)
    return Matriz(m, n, datos_a)


class ControladorTransformaciones:
    """Gestiona el análisis analítico de núcleo, imagen y dimensión de transformaciones."""

    @staticmethod
    def procesar(payload_json: str) -> str:
        """Parsea el payload y ejecuta el análisis algebraico de la transformación."""
        try:
            datos = json.loads(payload_json)
        except json.JSONDecodeError as error:
            return json.dumps({
                "status": "ERROR",
                "message": f"Payload JSON inválido: {error}",
            })

        a_raw = datos.get("A")
        if not a_raw or not isinstance(a_raw, list):
            return json.dumps({"status": "ERROR", "message": "Falta la matriz A."})

        try:
            matriz_a = _parsear_matriz_a(a_raw)
        except (ValueError, Exception) as error:
            return json.dumps({"status": "ERROR", "message": str(error)})

        variables = datos.get("variables") or None
        resolutor = ResolutorTransformacionesLineales()
        resultado = resolutor.resolver(matriz_a, variables)

        return json.dumps(resultado, ensure_ascii=False, default=str)
