"""Controlador de operaciones matriciales y evaluación de expresiones algebraicas."""
import json
import logging
import re
from typing import Any

from src.ai.contexto import sanear_cadena_usuario
from src.backend.resolutores.operaciones_matrices.evaluador import (
    EvaluadorExpresionesMatriciales,
)
from src.backend.resolutores.operaciones_matrices.captura_matrices import obtener_diccionario_matrices
from src.backend.resolutores.operaciones_matrices.estado_resultado import (
    calcular_banderas_resultado, preparar_transferencia_inversa,
)
from src.frontend.controladores.operaciones_matrices.codificador import (
    CodificadorMatriz,
)
from src.frontend.controladores.utilidades import parsear_carga_json

registro = logging.getLogger(__name__)


def _extraer_ejemplo_celda(pasos_celda: Any) -> str | None:
    """Extrae la primera descripción representativa de pasos por celda."""
    if not isinstance(pasos_celda, list):
        return None
    for paso_celda in pasos_celda:
        if isinstance(paso_celda, dict) and paso_celda.get("detalle_latex") and paso_celda.get("descripcion"):
            return sanear_cadena_usuario(paso_celda["descripcion"], 120)
    return None


class ControladorOperacionesMatrices:
    """Gestiona la validación y cálculo de expresiones entre múltiples matrices."""

    @staticmethod
    def procesar_expresion(expresion_texto: str, matrices_json: str) -> str:
        """Evalúa una expresión algebraica matricial y devuelve el resultado serializado."""
        datos_matrices, error = parsear_carga_json(matrices_json)
        if error:
            return error
        if datos_matrices is None:
            return json.dumps({"estado": "ERROR", "mensaje": "Datos de matrices vacíos."})

        try:
            matrices = obtener_diccionario_matrices(datos_matrices)
        except ValueError as error_captura:
            return json.dumps({"estado": "ERROR", "mensaje": str(error_captura)}, ensure_ascii=False)

        try:
            evaluador = EvaluadorExpresionesMatriciales()
            resultado = evaluador.evaluar(expresion_texto, matrices)
        except ValueError as error_captura:
            return json.dumps({"estado": "ERROR", "mensaje": str(error_captura)}, ensure_ascii=False)
        except (ZeroDivisionError, TypeError):
            registro.exception("Error al evaluar la expresión matricial")
            return json.dumps({
                "estado": "ERROR",
                "mensaje": "No se pudo evaluar la expresión. Revisa la sintaxis y las dimensiones.",
            }, ensure_ascii=False)

        try:
            resultado.update(calcular_banderas_resultado(resultado, expresion_texto))
            return json.dumps(resultado, ensure_ascii=False, cls=CodificadorMatriz)
        except (TypeError, ValueError):
            registro.exception("Error al serializar el resultado matricial")
            return json.dumps({
                "estado": "ERROR",
                "mensaje": "No se pudo serializar el resultado de la expresión.",
            }, ensure_ascii=False)

    @staticmethod
    def obtener_matrices_serializadas(datos_crudos: dict) -> dict:
        """Valida datos crudos y serializa matrices exactas; propaga ValueError de captura."""
        matrices = obtener_diccionario_matrices(datos_crudos)
        return json.loads(json.dumps(matrices, cls=CodificadorMatriz))

    @staticmethod
    def preparar_inversa(nombre: str, datos_matriz: dict) -> dict:
        """Delega las condiciones de transferencia y devuelve datos o mensaje."""
        return preparar_transferencia_inversa(nombre, datos_matriz)

    @staticmethod
    def construir_foco_paso(paso: dict, indice: int, total: int) -> dict:
        """Construye metadatos de foco y detalles simplificados para un paso de evaluación."""
        tipo_operacion = paso.get("tipo_operacion") or "Operación"
        representacion_operacion = paso.get("representacion_operacion") or ""
        operacion_cruda = f"{tipo_operacion}: {representacion_operacion}" if representacion_operacion else str(tipo_operacion)

        operacion_limpia = re.sub(r"_\{(\w+)\}", r"\1", operacion_cruda)
        operacion_limpia = operacion_limpia.replace(r"\cdot", "").replace("{", "").replace("}", "")
        operacion_limpia = " ".join(operacion_limpia.split())

        detalle = {}
        matriz_resultado = paso.get("matriz_resultado")
        if hasattr(matriz_resultado, "filas") and hasattr(matriz_resultado, "columnas"):
            detalle["forma"] = f"{matriz_resultado.filas}×{matriz_resultado.columnas}"
        elif isinstance(matriz_resultado, dict) and "filas" in matriz_resultado and "columnas" in matriz_resultado:
            detalle["forma"] = f"{matriz_resultado['filas']}×{matriz_resultado['columnas']}"

        ejemplo = _extraer_ejemplo_celda(paso.get("pasos_celda_a_celda"))
        if ejemplo:
            detalle["ejemplo"] = ejemplo

        return {
            "indice": indice,
            "total": total,
            "tipo": "otro",
            "operacion": operacion_limpia,
            "filas_antes": {},
            "filas_despues": {},
            "columnas": None,
            "detalle": detalle,
        }
