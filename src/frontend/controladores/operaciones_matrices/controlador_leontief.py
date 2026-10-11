"""Controlador del Modelo de Leontief para la capa de presentación."""
import json
from fractions import Fraction
import logging

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.leontief import (
    ResolutorModeloLeontief,
)
from src.backend.utilidades.validadores import ValidadorMatriz

logger = logging.getLogger(__name__)


def _parsear_matriz_c(c_raw: list) -> Matriz:
    """Valida y convierte la matriz de coeficientes técnicos a fracciones exactas."""
    n = len(c_raw)
    datos_c = []
    for i, fila in enumerate(c_raw):
        if len(fila) != n:
            raise ValueError(
                f"Fila {i+1} de C tiene {len(fila)} columnas; se esperaban {n}."
            )
        fila_parseada = []
        for j, raw in enumerate(fila):
            texto = str(raw).strip() if raw is not None else "0"
            ok, val, err = ValidadorMatriz.parsear_numero_exacto(texto)
            if not ok:
                raise ValueError(f"C[{i+1},{j+1}]: {err}")
            fila_parseada.append(val)
        datos_c.append(fila_parseada)
    return Matriz(n, n, datos_c)


def _parsear_vector_d(d_raw: list) -> list[Fraction]:
    """Valida y convierte el vector de demanda final a fracciones exactas."""
    vector_d = []
    for i, raw in enumerate(d_raw):
        texto = str(raw).strip() if raw is not None else "0"
        ok, val, err = ValidadorMatriz.parsear_numero_exacto(texto)
        if not ok:
            raise ValueError(f"d[{i+1}]: {err}")
        vector_d.append(val)
    return vector_d


class ControladorLeontief:
    """Gestiona el cálculo de producción y viabilidad del modelo insumo-producto de Leontief."""

    @staticmethod
    def procesar(payload_json: str) -> str:
        """Parsea el payload, ejecuta el modelo de Leontief y devuelve la respuesta JSON."""
        try:
            datos = json.loads(payload_json)
        except json.JSONDecodeError as error:
            return json.dumps({
                "status": "ERROR",
                "message": f"Payload JSON inválido: {error}",
            })

        c_raw = datos.get("C")
        if not c_raw or not isinstance(c_raw, list):
            return json.dumps({"status": "ERROR", "message": "Falta la matriz C."})

        d_raw = datos.get("d")
        if not d_raw or not isinstance(d_raw, list):
            return json.dumps({"status": "ERROR", "message": "Falta el vector d."})

        try:
            matriz_c = _parsear_matriz_c(c_raw)
            vector_d = _parsear_vector_d(d_raw)
        except (ValueError, Exception) as error:
            return json.dumps({"status": "ERROR", "message": str(error)})

        sectores = datos.get("sectores") or None
        resolutor = ResolutorModeloLeontief()
        resultado = resolutor.resolver(matriz_c, vector_d, sectores)

        return json.dumps(resultado, ensure_ascii=False, default=str)
