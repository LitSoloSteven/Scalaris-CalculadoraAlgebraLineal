"""Preparación del objetivo, generadores y cadena de una combinación lineal."""
from fractions import Fraction

from src.backend.excepciones import AlgebraLinealError
from src.backend.geometria.cadena_combinacion import calcular_cadena_acumulada
from src.backend.geometria.captura import ubicar_error_vector
from src.backend.geometria.coordenadas import a_flotante_seguro
from src.backend.geometria.errores import respuesta_error
from src.backend.geometria.recorte import calcular_rango_automatico
from src.backend.geometria.transferencia import LIMITES_VECTORES_ESCENA
from src.backend.resolutores.operaciones_vectores.captura import construir_vector_desde_diccionario
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal


def _parsear_vector(entrada, nombre):
    if not isinstance(entrada, dict):
        return None, respuesta_error("Datos de vector inválidos.")
    try:
        return construir_vector_desde_diccionario(entrada), None
    except ValueError as error:
        celda = ubicar_error_vector(nombre, entrada.get("datos", []))
        return None, respuesta_error(str(error), celda)


def _validar_entrada(datos):
    entradas = datos.get("vectores", [])
    minimo, maximo = LIMITES_VECTORES_ESCENA["combinacion"]
    if not isinstance(entradas, list) or not minimo - 1 <= len(entradas) <= maximo - 1:
        return None, None, respuesta_error("Se necesitan entre 1 y 4 vectores columna.")
    objetivo, error = _parsear_vector(datos.get("objetivo", {}), "b")
    if error or objetivo is None:
        return None, None, error
    dimension = objetivo.filas
    if dimension not in (2, 3):
        mensaje = f"Solo se grafican vectores de dimensión 2 o 3 (b tiene {dimension})."
        return None, None, respuesta_error(mensaje, codigo="dimension_invalida")
    columnas, error = _parsear_columnas(entradas, dimension)
    return objetivo, columnas, error


def _parsear_columnas(entradas, dimension):
    columnas = []
    for indice, entrada in enumerate(entradas):
        nombre = f"v_{indice+1}"
        columna, error = _parsear_vector(entrada, nombre)
        if error:
            return None, error
        if columna.filas != dimension:
            return None, respuesta_error(f"El vector {nombre} tiene dimensión {columna.filas}, pero b tiene {dimension}.")
        columnas.append(columna)
    return columnas, None


def preparar_escena_combinacion(datos: dict) -> dict:
    """Valida objetivo y columnas, resuelve y devuelve una escena exacta serializada."""
    objetivo, columnas, error = _validar_entrada(datos)
    if error or objetivo is None or columnas is None:
        return error or {}
    try:
        resultado = ResolutorCombinacionLineal().resolver(objetivo, columnas)
    except (AlgebraLinealError, ValueError) as error:
        return respuesta_error(str(error))
    return _construir_escena(objetivo, columnas, resultado)


def _construir_escena(objetivo, columnas, resultado):
    dimension = objetivo.filas
    objetivo_aproximado = _coordenadas(objetivo, dimension)
    vectores = [_coordenadas(columna, dimension) for columna in columnas]
    if not _coordenadas_representables(objetivo_aproximado, vectores):
        mensaje = "Algún valor es demasiado grande para graficarlo. Usa números más pequeños."
        return dict(respuesta_error(mensaje, codigo="no_finito"), numero_variables=dimension)
    estado = resultado.get("estado", "ERROR")
    cadena, extras = _serializar_cadena(resultado, columnas, dimension) if estado == "UNICA" else (None, [])
    valores = objetivo_aproximado + [valor for vector in vectores for valor in vector] + extras
    rango = calcular_rango_automatico(valores)
    geometria = (cadena, estado, rango, valores)
    return _respuesta_combinacion(objetivo, columnas, (objetivo_aproximado, vectores, dimension), geometria, resultado)


def _coordenadas_representables(objetivo, vectores):
    return all(valor is not None for valor in objetivo) and all(valor is not None for vector in vectores for valor in vector)


def _respuesta_combinacion(objetivo, columnas, coordenadas, geometria, resultado):
    objetivo_aproximado, vectores, dimension = coordenadas
    cadena, estado, rango, valores = geometria
    return {
        "estado": "EXITO", "numero_variables": dimension,
        "objetivo": _vector_serializable(objetivo, objetivo_aproximado, dimension),
        "vectores": [_vector_serializable(columna, vectores[indice], dimension) for indice, columna in enumerate(columnas)],
        "cadena": cadena, "representacion": "no_unica" if estado == "INFINITA" else None,
        "objetivo_fuera_del_espacio_generado": estado == "SIN_SOLUCION", "estado_solucion": estado,
        "rango": rango, "fuera_de_rango": any(abs(valor) > rango[1] for valor in valores),
        "celda_error": None, "mensaje": resultado.get("mensaje", ""),
    }


def _coordenadas(matriz, dimension):
    return [a_flotante_seguro(Fraction(matriz.obtener(indice, 0))) for indice in range(dimension)]


def _vector_serializable(matriz, aproximado, dimension):
    return {"aproximado": aproximado, "exacta": [str(matriz.obtener(indice, 0)) for indice in range(dimension)]}


def _serializar_cadena(resultado, columnas, dimension):
    cadena, valores = [], []
    for paso in calcular_cadena_acumulada(resultado, columnas, dimension):
        aproximado = [a_flotante_seguro(valor) for valor in paso.coordenadas]
        cadena.append({"aproximado": aproximado, "exacta": [str(valor) for valor in paso.coordenadas], "etiqueta": paso.etiqueta})
        valores.extend(valor for valor in aproximado if valor is not None)
    return cadena, valores
