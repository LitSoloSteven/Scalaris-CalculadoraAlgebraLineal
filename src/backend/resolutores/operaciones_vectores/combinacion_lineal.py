"""Resolutor de combinación lineal de vectores en R^n."""

from src.backend.constantes import INFINITA, UNICA

import re

from src.backend.constantes import (
    ERROR,
    SIN_SOLUCION,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)
from src.backend.excepciones import ErrorVectorInvalido
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import matriz_de_columnas
from src.backend.resolutores.sistemas_lineales.comprobacion_sistemas import comprobar_familia
from src.backend.resolutores.operaciones_matrices.comprobacion_productos import crear_paso_analisis
from src.backend.resolutores.operaciones_vectores.base import (
    _BaseResolutorVectores,
)
from src.backend.resolutores.operaciones_vectores.formateadores import (
    matriz_aumentada_gauss_a_latex,
)
from src.backend.resolutores.operaciones_vectores.planteamiento import (
    construir_paso_comprobacion,
    construir_pasos_planteamiento,
)
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def _limpiar_pasos_gauss(pasos_brutos: list[dict], numero_vectores: int) -> list[dict]:
    """Descarta el paso inicial redundante y normaliza descripciones y LaTeX."""
    limpios = []
    lista = pasos_brutos[1:] if len(pasos_brutos) > 1 else pasos_brutos
    for indice, paso in enumerate(lista, start=1):
        matriz_paso = paso.get("matriz")
        matriz_latex = paso.get("detalle_latex")
        if not matriz_latex and matriz_paso:
            matriz_latex = matriz_aumentada_gauss_a_latex(matriz_paso, numero_vectores)
        desc_bruta = paso.get("descripcion", "")
        desc_limpia = re.sub(r"^\d+\.\s*", "", desc_bruta)
        limpios.append({
            "numero_paso": indice,
            "descripcion": desc_limpia,
            "matriz": matriz_paso.clonar() if matriz_paso else None,
            "detalle_latex": matriz_latex,
        })
    return limpios


def _construir_error_combinacion_lineal(mensaje: str) -> dict:
    """Construye la respuesta estructurada de error."""
    return {
        "estado": ERROR,
        "es_combinacion_lineal": False,
        "coeficientes": None,
        "coeficientes_texto": None,
        "solucion_parametrica": None,
        "parametros_libres": [],
        "mensaje": mensaje,
        "pasos_planteamiento": [],
        "pasos": [],
        "pasos_gauss": [],
        "pasos_sustitucion_regresiva": [],
        "paso_verificacion": None,
    }


def _construir_aumentada(objetivo: Matriz, vectores: list[Matriz]) -> Matriz:
    """Construye la matriz aumentada [v_1 | ... | v_k | b]."""
    return matriz_de_columnas(vectores + [objetivo])


def _validar_listas_nombres(
    numero_vectores: int,
    variables: list[str] | None,
    vectores: list[str] | None,
) -> str | None:
    """Valida tamaños y tipos de las listas de nombres opcionales."""
    for nombre, lista in (("nombres_variables", variables), ("nombres_vectores", vectores)):
        if lista is not None:
            if not isinstance(lista, list):
                return f"{nombre} debe ser una lista."
            if len(lista) != numero_vectores:
                return f"{nombre} tiene {len(lista)} nombres; se esperaban {numero_vectores} (uno por vector)."
    return None


def _empaquetar_unica(
    objetivo: Matriz,
    vectores: list[Matriz],
    configuracion: tuple[list[str], list[str], str],
    resultado_gauss: dict,
    pasos_agrupados: tuple[list[dict], list[dict], list[dict]],
) -> dict:
    """Empaqueta el resultado cuando existe combinación lineal única."""
    variables_efectivas, nombres_vectores_efectivos, sujeto = configuracion
    planteamiento, gauss_limpios, combinados = pasos_agrupados
    coeficientes = list(resultado_gauss.get("solucion_exacta", []))
    coeficientes_texto = list(resultado_gauss.get("solucion", []))
    verificacion = construir_paso_comprobacion(objetivo, vectores, coeficientes, variables_efectivas, nombres_vectores_efectivos)
    mensaje_resultado = f"b es combinación lineal {sujeto} (representación única)."
    return {
        "estado": UNICA,
        "es_combinacion_lineal": True,
        "coeficientes": coeficientes,
        "coeficientes_texto": coeficientes_texto,
        "solucion_parametrica": None,
        "parametros_libres": [],
        "mensaje": mensaje_resultado,
        "pasos_planteamiento": planteamiento,
        "pasos": combinados,
        "pasos_gauss": gauss_limpios,
        "pasos_sustitucion_regresiva": resultado_gauss.get("pasos_sustitucion_regresiva", []),
        "paso_verificacion": verificacion,
    }


def _empaquetar_infinitas(
    configuracion: tuple[list[str], str],
    resultado_gauss: dict,
    pasos_agrupados: tuple[list[dict], list[dict], list[dict]],
) -> dict:
    """Empaqueta el resultado cuando hay infinitas combinaciones lineales."""
    variables_efectivas, sujeto = configuracion
    planteamiento, gauss_limpios, combinados = pasos_agrupados
    solucion = list(resultado_gauss.get("solucion", []))
    columnas_libres = resultado_gauss.get("columnas_libres") or []
    libres = [variables_efectivas[c] for c in columnas_libres]
    mensaje_resultado = f"b es combinación lineal {sujeto}. Existen infinitas representaciones; se muestra la paramétrica."
    return {
        "estado": INFINITA,
        "es_combinacion_lineal": True,
        "coeficientes": None,
        "coeficientes_texto": None,
        "solucion_parametrica": solucion,
        "parametros_libres": libres,
        "mensaje": mensaje_resultado,
        "pasos_planteamiento": planteamiento,
        "pasos": combinados,
        "pasos_gauss": gauss_limpios,
        "pasos_sustitucion_regresiva": resultado_gauss.get("pasos_sustitucion_regresiva", []),
        "paso_verificacion": None,
    }


def _empaquetar_sin_solucion(
    sujeto: str,
    pasos_agrupados: tuple[list[dict], list[dict], list[dict]],
) -> dict:
    """Empaqueta el resultado cuando no existe combinación lineal."""
    planteamiento, gauss_limpios, combinados = pasos_agrupados
    mensaje_resultado = f"b NO es combinación lineal {sujeto}."
    return {
        "estado": SIN_SOLUCION,
        "es_combinacion_lineal": False,
        "coeficientes": None,
        "coeficientes_texto": None,
        "solucion_parametrica": None,
        "parametros_libres": [],
        "mensaje": mensaje_resultado,
        "pasos_planteamiento": planteamiento,
        "pasos": combinados,
        "pasos_gauss": gauss_limpios,
        "pasos_sustitucion_regresiva": [],
        "paso_verificacion": None,
    }


def _combinar_pasos_vectoriales(planteamiento: list[dict], gauss: list[dict]) -> list[dict]:
    """Combina pasos de planteamiento y pasos gaussianos con numeración continua."""
    combinados = [dict(paso) for paso in planteamiento]
    for indice, paso_gauss in enumerate(gauss, start=len(planteamiento) + 1):
        s_copia = dict(paso_gauss)
        s_copia["numero_paso"] = indice
        combinados.append(s_copia)
    return combinados


def _comprobar_familia_vectorial(respuesta: dict, vectores: list, objetivo: Matriz, resultado: dict) -> dict:
    comprobacion = comprobar_familia(matriz_de_columnas(vectores).datos, [fila[0] for fila in objetivo.datos], resultado["parametros_solucion"])
    respuesta["traza_comprobacion"] = [crear_paso_analisis(f"Componente {indice+1}: Ac=b", detalle,
                                                         "Agrupamos la constante y los parametros para comprobar la igualdad para toda la familia.", "verificacion")
                                        for indice, detalle in enumerate(comprobacion["pasos_latex"])]
    return respuesta


class ResolutorCombinacionLineal(_BaseResolutorVectores):
    """Determina si un vector b es combinación lineal de un conjunto de vectores."""

    def _validar_dimensiones_vectores(self, objetivo: Matriz, vectores: list[Matriz]) -> str | None:
        """Verifica compatibilidad de dimensiones de columna entre b y vectores."""
        try:
            self.validar_vector_columna(objetivo, "b")
            dimension = objetivo.filas
            for i, vector in enumerate(vectores):
                self.validar_vector_columna(vector, f"v_{i + 1}")
                if vector.filas != dimension:
                    return f"Dimensiones incompatibles: b tiene dim {dimension}, v_{i + 1} tiene dim {vector.filas}."
        except ErrorVectorInvalido as error:
            return str(error)
        return None

    def _validar_entradas(
        self,
        objetivo: Matriz,
        vectores: list[Matriz],
        nombres_variables: list[str] | None,
        nombres_vectores: list[str] | None,
    ) -> str | None:
        """Valida que los vectores y nombres cumplan los invariantes de dimensión."""
        if not isinstance(vectores, list) or len(vectores) == 0:
            return "Se requiere al menos un vector."
        error_nombres = _validar_listas_nombres(len(vectores), nombres_variables, nombres_vectores)
        if error_nombres:
            return error_nombres
        return self._validar_dimensiones_vectores(objetivo, vectores)

    def resolver(
        self,
        objetivo: Matriz,
        vectores: list[Matriz],
        *,
        nombres_variables: list[str] | None = None,
        nombres_vectores: list[str] | None = None,
    ) -> dict:
        """Determina si b es combinación lineal de vectores mediante eliminación de Gauss."""
        error = self._validar_entradas(objetivo, vectores, nombres_variables, nombres_vectores)
        if error:
            return _construir_error_combinacion_lineal(error)

        numero_vectores = len(vectores)
        sujeto = "del vector" if numero_vectores == 1 else f"de los {numero_vectores} vectores"
        variables_efectivas = nombres_variables if nombres_variables else [f"c_{j + 1}" for j in range(numero_vectores)]
        nombres_vectores_efectivos = nombres_vectores if nombres_vectores else [f"v_{j + 1}" for j in range(numero_vectores)]

        aumentada = _construir_aumentada(objetivo, vectores)
        planteamiento = construir_pasos_planteamiento(objetivo, vectores, variables_efectivas, aumentada=aumentada)

        resolutor_g = ResolutorGauss(aumentada, nombres_variables=variables_efectivas)
        resultado_gauss = resolutor_g.resolver()
        gauss_limpios = _limpiar_pasos_gauss(resultado_gauss.get("pasos", []), numero_vectores)
        pasos_combinados = _combinar_pasos_vectoriales(planteamiento, gauss_limpios)

        estado_g = resultado_gauss["estado"]
        agrupados = (planteamiento, gauss_limpios, pasos_combinados)
        if estado_g == SOLUCION_UNICA:
            return _empaquetar_unica(objetivo, vectores, (variables_efectivas, nombres_vectores_efectivos, sujeto), resultado_gauss, agrupados)
        if estado_g == SOLUCIONES_INFINITAS:
            respuesta = _empaquetar_infinitas((variables_efectivas, sujeto), resultado_gauss, agrupados)
            return _comprobar_familia_vectorial(respuesta, vectores, objetivo, resultado_gauss)
        return _empaquetar_sin_solucion(sujeto, agrupados)

