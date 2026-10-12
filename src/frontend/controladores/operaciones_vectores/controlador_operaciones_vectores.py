"""Controlador para operaciones vectoriales y combinación lineal pedagógica."""
import json
import logging

from src.backend.excepciones import AlgebraLinealError
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import (
    ResolutorCombinacionLineal,
)
from src.backend.resolutores.operaciones_vectores.captura import construir_vector_desde_dict
from src.backend.resolutores.operaciones_vectores.operaciones import (
    ResolutorOperacionesVectores,
)
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion
from src.frontend.controladores.operaciones_matrices.codificador import (
    CodificadorMatriz,
)
from src.frontend.controladores.sistemas_lineales.compartido import (
    construir_metadatos_pasos,
)
from src.frontend.controladores.utilidades import (
    construir_vista_pasos,
    parsear_payload,
)

logger = logging.getLogger(__name__)


def _asegurar_latex_en_paso(paso: dict) -> None:
    """Garantiza la representacion LaTeX de una matriz en el paso si no existe."""
    mat = paso.pop("matrix", None)
    if mat is not None and not paso.get("detail_latex"):
        paso["detail_latex"] = matriz_a_latex(mat)


def _enriquecer_respuesta_combinacion(res: dict, vectores: list[Matriz]) -> None:
    """Agrega metadatos pedagógicos y vistas de pasos a la combinación lineal."""
    pasos_setup = res.get("setup_steps", [])
    pasos_gauss = res.get("gauss_steps", [])
    matriz_inicial = pasos_setup[-1].get("matrix") if pasos_setup else None

    if pasos_gauss:
        res["steps_meta"] = construir_metadatos_pasos(pasos_gauss, matriz_inicial=matriz_inicial)
    elif "steps" in res:
        res["steps_meta"] = construir_metadatos_pasos(res["steps"])

    n_vars = len(vectores)
    res["n_vars"] = n_vars
    res["variables"] = [f"c_{i+1}" for i in range(n_vars)]

    pasos_clasificados, grupos, stats = agrupar_pasos_eliminacion(
        pasos_gauss, n_vars, res.get("status"), contexto="sistema", metodo="gauss"
    )
    res["steps_view"] = construir_vista_pasos(pasos_clasificados)
    res["groups"] = grupos
    res["stats"] = stats

    for lista_pasos in (pasos_setup, pasos_gauss, res.get("steps", [])):
        for paso in lista_pasos:
            _asegurar_latex_en_paso(paso)


class ControladorOperacionesVectores:
    """Gestiona la ejecución de operaciones básicas entre vectores y combinaciones lineales."""

    @staticmethod
    def procesar_suma_resta(payload_str: str) -> str:
        """Calcula la suma o resta entre dos vectores y devuelve los pasos."""
        datos, err = parsear_payload(payload_str)
        if err or datos is None:
            return err or "{}"

        try:
            op = datos.get("operation")
            v1 = construir_vector_desde_dict(datos.get("v1", {}))
            v2 = construir_vector_desde_dict(datos.get("v2", {}))
            estricto = datos.get("strict", False)

            resolutor = ResolutorOperacionesVectores()
            if op == "add":
                res = resolutor.sumar(v1, v2, nombre1="v_1", nombre2="v_2", estricto=estricto)
            else:
                res = resolutor.restar(v1, v2, nombre1="v_1", nombre2="v_2", estricto=estricto)

            for paso in res.get("steps", []):
                paso.pop("matrix", None)
            res.pop("result_matrix", None)

            return json.dumps(res, cls=CodificadorMatriz)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en procesar_suma_resta")
            return json.dumps({
                "status": "ERROR",
                "message": "Ocurrió un error inesperado al procesar la operación. Inténtalo de nuevo.",
            })

    @staticmethod
    def procesar_multiplicacion_escalar(payload_str: str) -> str:
        """Calcula la multiplicación de un vector por un escalar exacto."""
        datos, err = parsear_payload(payload_str)
        if err or datos is None:
            return err or "{}"

        try:
            escalar_str = str(datos.get("scalar", "0"))
            exito, k, msg = ValidadorMatriz.parsear_numero_exacto(escalar_str)
            if not exito:
                return json.dumps({"status": "ERROR", "message": f"Escalar inválido: {msg}"})

            v = construir_vector_desde_dict(datos.get("v", {}))
            resolutor = ResolutorOperacionesVectores()
            res = resolutor.multiplicar_escalar(k, v, nombre="v", nombre_resultado="w")

            for paso in res.get("steps", []):
                paso.pop("matrix", None)
            res.pop("result_matrix", None)

            return json.dumps(res, cls=CodificadorMatriz)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en procesar_multiplicacion_escalar")
            return json.dumps({
                "status": "ERROR",
                "message": "Ocurrió un error inesperado al procesar la multiplicación por escalar. Inténtalo de nuevo.",
            })

    @classmethod
    def procesar_combinacion_lineal(cls, payload_str: str) -> str:
        """Determina los coeficientes que expresan a un vector b como combinación de otros."""
        datos, err = parsear_payload(payload_str)
        if err or datos is None:
            return err or "{}"

        try:
            b = construir_vector_desde_dict(datos.get("b", {}))
            vectores = [construir_vector_desde_dict(v) for v in datos.get("vectors", [])]
            resolutor = ResolutorCombinacionLineal()
            res = resolutor.resolver(b, vectores)
            _enriquecer_respuesta_combinacion(res, vectores)

            return json.dumps(res, cls=CodificadorMatriz)
        except (AlgebraLinealError, ValueError) as e:
            return json.dumps({"status": "ERROR", "message": str(e)})
        except Exception:
            logger.exception("Error inesperado en procesar_combinacion_lineal")
            return json.dumps({
                "status": "ERROR",
                "message": "Ocurrió un error inesperado al resolver la combinación lineal. Inténtalo de nuevo.",
            })
