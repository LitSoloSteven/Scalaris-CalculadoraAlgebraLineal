"""Controlador para operaciones vectoriales y combinación lineal pedagógica."""
import json
import logging

from src.backend.excepciones import AlgebraLinealError
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import (
    ResolutorCombinacionLineal,
)
from src.backend.resolutores.operaciones_vectores.captura import (
    construir_vector_desde_diccionario, parsear_escalar_capturado, validar_carga_vectorial,
)
from src.backend.resolutores.operaciones_vectores.operaciones import (
    ResolutorOperacionesVectores,
)
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion
from src.frontend.controladores.operaciones_matrices.codificador import (
    CodificadorMatriz,
)
from src.frontend.controladores.sistemas_lineales.compartido import (
    construir_metadatos_pasos,
)
from src.frontend.controladores.utilidades import (
    construir_vista_pasos,
    parsear_carga_json,
)

registro = logging.getLogger(__name__)


def _asegurar_latex_en_paso(paso: dict) -> None:
    """Garantiza la representacion LaTeX de una matriz en el paso si no existe."""
    matriz = paso.pop("matriz", None)
    if matriz is not None and not paso.get("detalle_latex"):
        paso["detalle_latex"] = matriz_a_latex(matriz)


def _enriquecer_respuesta_combinacion(resultado: dict, vectores: list[Matriz]) -> None:
    """Agrega metadatos pedagógicos y vistas de pasos a la combinación lineal."""
    pasos_planteamiento = resultado.get("pasos_planteamiento", [])
    pasos_gauss = resultado.get("pasos_gauss", [])
    matriz_inicial = pasos_planteamiento[-1].get("matriz") if pasos_planteamiento else None

    if pasos_gauss:
        resultado["metadatos_pasos"] = construir_metadatos_pasos(pasos_gauss, matriz_inicial=matriz_inicial)
    elif "pasos" in resultado:
        resultado["metadatos_pasos"] = construir_metadatos_pasos(resultado["pasos"])

    numero_variables = len(vectores)
    resultado["numero_variables"] = numero_variables
    resultado["variables"] = [f"c_{i+1}" for i in range(numero_variables)]

    pasos_clasificados, grupos, estadisticas = agrupar_pasos_eliminacion(
        pasos_gauss, numero_variables, resultado.get("estado"), contexto="sistema", metodo="gauss"
    )
    resultado["vista_pasos"] = construir_vista_pasos(pasos_clasificados)
    resultado["grupos"] = grupos
    resultado["estadisticas"] = estadisticas

    for lista_pasos in (pasos_planteamiento, pasos_gauss, resultado.get("pasos", [])):
        for paso in lista_pasos:
            _asegurar_latex_en_paso(paso)


class ControladorOperacionesVectores:
    """Gestiona la ejecución de operaciones básicas entre vectores y combinaciones lineales."""

    @staticmethod
    def procesar_suma_resta(carga_texto: str) -> str:
        """Calcula la suma o resta entre dos vectores y devuelve los pasos."""
        datos, error = parsear_carga_json(carga_texto)
        if error or datos is None:
            return error or "{}"

        try:
            validar_carga_vectorial(datos, "suma_resta")
            operacion = datos.get("operacion")
            v1 = construir_vector_desde_diccionario(datos.get("vector_1", {}))
            v2 = construir_vector_desde_diccionario(datos.get("vector_2", {}))
            estricto = datos.get("estricto", False)

            resolutor = ResolutorOperacionesVectores()
            if operacion == "suma":
                resultado = resolutor.sumar(v1, v2, nombre1="v_1", nombre2="v_2", estricto=estricto)
            else:
                resultado = resolutor.restar(v1, v2, nombre1="v_1", nombre2="v_2", estricto=estricto)

            for paso in resultado.get("pasos", []):
                paso.pop("matriz", None)

            return json.dumps(resultado, cls=CodificadorMatriz)
        except (AlgebraLinealError, ValueError) as error_captura:
            return json.dumps({"estado": "ERROR", "mensaje": str(error_captura)})
        except Exception:
            registro.exception("Error inesperado en procesar_suma_resta")
            return json.dumps({
                "estado": "ERROR",
                "mensaje": "Ocurrió un error inesperado al procesar la operación. Inténtalo de nuevo.",
            })

    @staticmethod
    def procesar_multiplicacion_escalar(carga_texto: str) -> str:
        """Calcula la multiplicación de un vector por un escalar exacto."""
        datos, error = parsear_carga_json(carga_texto)
        if error or datos is None:
            return error or "{}"

        try:
            validar_carga_vectorial(datos, "escalar")
            escalar = parsear_escalar_capturado(datos.get("escalar", "0"))
            vector = construir_vector_desde_diccionario(datos.get("vector", {}))
            resolutor = ResolutorOperacionesVectores()
            resultado = resolutor.multiplicar_escalar(escalar, vector, nombre="v", nombre_resultado="w")

            for paso in resultado.get("pasos", []):
                paso.pop("matriz", None)

            return json.dumps(resultado, cls=CodificadorMatriz)
        except (AlgebraLinealError, ValueError) as error_captura:
            return json.dumps({"estado": "ERROR", "mensaje": str(error_captura)})
        except Exception:
            registro.exception("Error inesperado en procesar_multiplicacion_escalar")
            return json.dumps({
                "estado": "ERROR",
                "mensaje": "Ocurrió un error inesperado al procesar la multiplicación por escalar. Inténtalo de nuevo.",
            })

    @classmethod
    def procesar_combinacion_lineal(cls, carga_texto: str) -> str:
        """Determina los coeficientes que expresan a un vector b como combinación de otros."""
        datos, error = parsear_carga_json(carga_texto)
        if error or datos is None:
            return error or "{}"

        try:
            validar_carga_vectorial(datos, "combinacion_lineal")
            objetivo = construir_vector_desde_diccionario(datos.get("objetivo", {}))
            vectores = [construir_vector_desde_diccionario(datos_vector) for datos_vector in datos.get("vectores", [])]
            resolutor = ResolutorCombinacionLineal()
            resultado = resolutor.resolver(objetivo, vectores)
            _enriquecer_respuesta_combinacion(resultado, vectores)

            return json.dumps(resultado, cls=CodificadorMatriz)
        except (AlgebraLinealError, ValueError) as error_captura:
            return json.dumps({"estado": "ERROR", "mensaje": str(error_captura)})
        except Exception:
            registro.exception("Error inesperado en procesar_combinacion_lineal")
            return json.dumps({
                "estado": "ERROR",
                "mensaje": "Ocurrió un error inesperado al resolver la combinación lineal. Inténtalo de nuevo.",
            })
