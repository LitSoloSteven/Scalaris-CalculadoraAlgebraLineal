"""Controlador de operaciones matriciales y evaluación de expresiones algebraicas."""
import json
import logging
import re
from typing import Any

from src.ai.contexto import sanear_cadena_usuario
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.evaluador import (
    EvaluadorExpresionesMatriciales,
)
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.operaciones_matrices.codificador import (
    CodificadorMatriz,
)
from src.frontend.controladores.utilidades import parsear_payload

logger = logging.getLogger(__name__)


def _validar_forma_matriz(nombre: str, mat_data: dict) -> tuple[int, int, list]:
    """Valida los campos obligatorios y tipos de una matriz en el payload."""
    if not isinstance(mat_data, dict):
        raise ValueError(f"Matriz '{nombre}': se esperaba un objeto con rows/cols/data.")
    filas = mat_data.get("rows")
    columnas = mat_data.get("cols")
    datos = mat_data.get("data")
    if not isinstance(filas, int) or filas <= 0:
        raise ValueError(f"Matriz '{nombre}': 'rows' debe ser un entero positivo.")
    if not isinstance(columnas, int) or columnas <= 0:
        raise ValueError(f"Matriz '{nombre}': 'cols' debe ser un entero positivo.")
    if not isinstance(datos, list):
        raise ValueError(f"Matriz '{nombre}': 'data' debe ser una lista de filas.")
    if len(datos) != filas:
        raise ValueError(f"Matriz '{nombre}': 'data' tiene {len(datos)} filas; se esperaban {filas}.")
    return filas, columnas, datos


def _parsear_filas_matriz(nombre: str, datos: list, filas: int, columnas: int) -> list[list]:
    """Convierte las celdas de una matriz a fracciones exactas."""
    filas_parseadas = []
    for i, fila in enumerate(datos):
        if not isinstance(fila, list):
            raise ValueError(f"Matriz '{nombre}': fila {i + 1} no es una lista.")
        if len(fila) != columnas:
            raise ValueError(f"Matriz '{nombre}': fila {i + 1} tiene {len(fila)} columnas; se esperaban {columnas}.")
        fila_actual = []
        for j, celda in enumerate(fila):
            texto = str(celda).strip() if celda is not None and str(celda).strip() else "0"
            ok, val, err = ValidadorMatriz.parsear_numero_exacto(texto)
            if not ok:
                raise ValueError(f"Matriz {nombre}, celda [{i + 1},{j + 1}]: {err}")
            fila_actual.append(val)
        filas_parseadas.append(fila_actual)
    return filas_parseadas


def _construir_matrices(datos_matrices: dict) -> dict[str, Matriz]:
    """Construye instancias de Matriz a partir de los datos parseados."""
    if not isinstance(datos_matrices, dict):
        raise ValueError("El payload debe contener un diccionario de matrices.")
    if not datos_matrices:
        raise ValueError("No se recibió ninguna matriz para evaluar.")

    matrices = {}
    for nombre, mat_data in datos_matrices.items():
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("Cada matriz debe tener un nombre no vacío.")
        filas, columnas, datos = _validar_forma_matriz(nombre, mat_data)
        datos_parseados = _parsear_filas_matriz(nombre, datos, filas, columnas)
        matrices[nombre] = Matriz(filas=filas, columnas=columnas, datos=datos_parseados)
    return matrices


def _extraer_ejemplo_celda(pasos_celda: Any) -> str | None:
    """Extrae la primera descripción representativa de pasos por celda."""
    if not isinstance(pasos_celda, list):
        return None
    for pc in pasos_celda:
        if isinstance(pc, dict) and pc.get("detail_latex") and pc.get("description"):
            return sanear_cadena_usuario(pc["description"], 120)
    return None


class ControladorOperacionesMatrices:
    """Gestiona la validación y cálculo de expresiones entre múltiples matrices."""

    _construir_matrices = staticmethod(_construir_matrices)

    @staticmethod
    def procesar_expresion(expresion_str: str, matrices_dict_json: str) -> str:
        """Evalúa una expresión algebraica matricial y devuelve el resultado serializado."""
        datos_matrices, err = parsear_payload(matrices_dict_json)
        if err:
            return err
        if datos_matrices is None:
            return json.dumps({"status": "ERROR", "message": "Datos de matrices vacíos."})

        try:
            matrices = _construir_matrices(datos_matrices)
        except ValueError as e:
            return json.dumps({"status": "ERROR", "message": str(e)}, ensure_ascii=False)

        try:
            evaluador = EvaluadorExpresionesMatriciales()
            resultado = evaluador.evaluar(expresion_str, matrices)
        except ValueError as e:
            return json.dumps({"status": "ERROR", "message": str(e)}, ensure_ascii=False)
        except (ZeroDivisionError, TypeError):
            logger.exception("Error al evaluar la expresión matricial")
            return json.dumps({
                "status": "ERROR",
                "message": "No se pudo evaluar la expresión. Revisa la sintaxis y las dimensiones.",
            }, ensure_ascii=False)

        try:
            return json.dumps(resultado, ensure_ascii=False, cls=CodificadorMatriz)
        except (TypeError, ValueError):
            logger.exception("Error al serializar el resultado matricial")
            return json.dumps({
                "status": "ERROR",
                "message": "No se pudo serializar el resultado de la expresión.",
            }, ensure_ascii=False)

    @staticmethod
    def construir_foco_paso(paso: dict, indice: int, total: int) -> dict:
        """Construye metadatos de foco y detalles simplificados para un paso de evaluación."""
        tipo_op = paso.get("operation_type") or "Operación"
        disp_op = paso.get("operation_display") or ""
        op_cruda = f"{tipo_op}: {disp_op}" if disp_op else str(tipo_op)

        op_limpia = re.sub(r"_\{(\w+)\}", r"\1", op_cruda)
        op_limpia = op_limpia.replace(r"\cdot", "").replace("{", "").replace("}", "")
        op_limpia = " ".join(op_limpia.split())

        detalle = {}
        mat_res = paso.get("result_matrix")
        if hasattr(mat_res, "filas") and hasattr(mat_res, "columnas"):
            detalle["forma"] = f"{mat_res.filas}×{mat_res.columnas}"
        elif isinstance(mat_res, dict) and "rows" in mat_res and "cols" in mat_res:
            detalle["forma"] = f"{mat_res['rows']}×{mat_res['cols']}"

        ejemplo = _extraer_ejemplo_celda(paso.get("cell_by_cell_steps"))
        if ejemplo:
            detalle["ejemplo"] = ejemplo

        return {
            "index": indice,
            "total": total,
            "kind": "otro",
            "op": op_limpia,
            "rows_before": {},
            "rows_after": {},
            "cols": None,
            "detail": detalle,
        }
