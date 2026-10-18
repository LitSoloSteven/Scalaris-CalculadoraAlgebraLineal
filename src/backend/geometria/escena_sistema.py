"""Resolución y preparación de una escena geométrica de ecuaciones lineales."""
import json

from src.backend.geometria.captura import ubicar_error_celda
from src.backend.geometria.clasificacion import detectar_paralelismo
from src.backend.geometria.conjunto_solucion import (
    construir_conjunto_desde_gauss, construir_conjunto_desde_parametros,
    obtener_parametros_solucion, validar_solucion_parametrica,
)
from src.backend.geometria.coordenadas import a_flotante_seguro
from src.backend.geometria.ecuaciones import construir_ecuaciones
from src.backend.geometria.errores import respuesta_error
from src.backend.geometria.recorte import calcular_rango_automatico
from src.backend.geometria.representacion_conjunto import representar_conjunto
from src.backend.resolutores.sistemas_lineales.captura import validar_y_construir_aumentada
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def preparar_escena_sistema(datos: dict) -> dict:
    """Valida A y b, resuelve exactamente y devuelve una escena serializable."""
    aumentada, coeficientes, independientes, cantidad, dimension, error = validar_y_construir_aumentada(datos)
    if _fallo_captura(error, coeficientes, independientes, aumentada):
        mensaje = json.loads(error).get("mensaje", "") if error else ""
        celda = ubicar_error_celda(datos.get("matriz_a", []), datos.get("vector_b", []))
        return respuesta_error(mensaje, celda)
    if dimension not in (2, 3):
        mensaje = f"Este visualizador solo grafica sistemas con 2 o 3 variables (el tuyo tiene {dimension}). Puedes resolverlo en Sistemas de ecuaciones."
        return dict(respuesta_error(mensaje, codigo="dimension_invalida"), numero_variables=dimension)
    ecuaciones, valores = construir_ecuaciones(coeficientes, independientes, dimension)
    if ecuaciones is None:
        mensaje = "Algún valor es demasiado grande para graficarlo. Usa números más pequeños."
        return dict(respuesta_error(mensaje, codigo="no_finito"), numero_variables=dimension)
    estado, conjunto, parametros, pendiente = _resolver_solucion(aumentada, coeficientes, independientes)
    _acumular_punto(conjunto, valores)
    rango = calcular_rango_automatico([valor for valor in valores if valor is not None])
    banderas = _determinar_banderas(dimension, estado, coeficientes, independientes)
    datos_solucion = (estado, conjunto, parametros, pendiente)
    return _respuesta_sistema(ecuaciones, datos_solucion, (dimension, cantidad), (rango, valores), banderas)


def _fallo_captura(error, coeficientes, independientes, aumentada):
    return bool(error) or coeficientes is None or independientes is None or aumentada is None


def _determinar_banderas(dimension, estado, coeficientes, independientes):
    if dimension == 2 and estado == "SIN_SOLUCION" and detectar_paralelismo(coeficientes, independientes):
        return ["paralelas"]
    return []


def _respuesta_sistema(ecuaciones, datos_solucion, dimensiones, ejes, banderas):
    estado, conjunto, parametros, pendiente = datos_solucion
    dimension, cantidad = dimensiones
    rango, valores = ejes
    return {
        "estado": "EXITO", "numero_variables": dimension, "numero_ecuaciones": cantidad,
        "ecuaciones": ecuaciones, "estado_solucion": estado,
        "conjunto_solucion": representar_conjunto(conjunto, parametros, dimension, rango[1]),
        "parametro_pendiente": pendiente, "banderas": banderas, "rango": rango,
        "fuera_de_rango": any(abs(valor) > rango[1] for valor in valores if valor is not None),
        "celda_error": None, "mensaje": "",
    }


def _resolver_solucion(aumentada, coeficientes, independientes):
    resultado = ResolutorGauss(aumentada).resolver()
    estado = resultado.get("estado")
    conjunto = construir_conjunto_desde_gauss(resultado)
    parametros, pendiente = None, False
    if estado == "SOLUCIONES_INFINITAS":
        parametros = obtener_parametros_solucion(resultado)
        if parametros and validar_solucion_parametrica(coeficientes, independientes, parametros["particular"], parametros["direcciones"]):
            conjunto = construir_conjunto_desde_parametros(parametros)
        else:
            pendiente, conjunto, parametros = True, None, None
    return estado, conjunto, parametros, pendiente


def _acumular_punto(conjunto, valores):
    if conjunto and conjunto.punto:
        for componente in conjunto.punto:
            aproximado = a_flotante_seguro(componente)
            if aproximado is not None:
                valores.append(aproximado)
