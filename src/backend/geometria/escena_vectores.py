"""Preparación exacta de la escena de escalamiento y suma de dos vectores."""
from src.backend.geometria.captura import parsear_par_vectores
from src.backend.geometria.coordenadas import a_flotante_seguro
from src.backend.geometria.cuadros_vectores import calcular_cuadros_vectores, calcular_suma_vectores
from src.backend.geometria.errores import respuesta_error
from src.backend.geometria.recorte import calcular_rango_automatico
from src.backend.geometria.transferencia import LIMITES_VECTORES_ESCENA

CUADRO_PREDETERMINADO = 16


def preparar_escena_vectores(datos: dict) -> dict:
    """Valida dos vectores, calcula sus cuadros y devuelve coordenadas serializables."""
    entradas = datos.get("vectores", [])
    minimo, maximo = LIMITES_VECTORES_ESCENA["vectores"]
    if not isinstance(entradas, list) or not minimo <= len(entradas) <= maximo:
        return respuesta_error("Se necesitan exactamente 2 vectores.")
    vectores, error = parsear_par_vectores(entradas)
    if error or vectores is None:
        return error or {}
    primero, segundo = vectores
    dimension = len(primero)
    if dimension != len(segundo):
        return respuesta_error("Los vectores deben tener la misma dimensión.")
    if dimension not in (2, 3):
        return respuesta_error(f"Solo se grafican vectores de dimensión 2 o 3 (los tuyos tienen {dimension}).", codigo="dimension_invalida")
    return _construir_escena(primero, segundo, dimension)


def _construir_escena(primero, segundo, dimension):
    aproximado_primero = [a_flotante_seguro(valor) for valor in primero]
    aproximado_segundo = [a_flotante_seguro(valor) for valor in segundo]
    suma = [a_flotante_seguro(valor) for valor in calcular_suma_vectores(primero, segundo)]
    valores = aproximado_primero + aproximado_segundo + suma
    if any(valor is None for valor in valores):
        return respuesta_error("Las coordenadas generan valores no finitos.", codigo="no_finito")
    cuadros, valores = _serializar_cuadros(primero, segundo, valores)
    rango = calcular_rango_automatico(valores)
    return {
        "estado": "EXITO", "numero_variables": dimension,
        "vector_u": {"aproximado": aproximado_primero, "exacta": [str(valor) for valor in primero]},
        "vector_v": {"aproximado": aproximado_segundo, "exacta": [str(valor) for valor in segundo]},
        "estatica": {"vector_u": aproximado_primero, "vector_v": aproximado_segundo, "u_mas_v": suma},
        "cuadros": cuadros, "cuadro_predeterminado": CUADRO_PREDETERMINADO, "rango": rango,
        "fuera_de_rango": any(abs(valor) > rango[1] for valor in valores if valor is not None),
        "celda_error": None, "mensaje": "",
    }


def _serializar_cuadros(primero, segundo, valores):
    cuadros = []
    valores = list(valores)
    for cuadro in calcular_cuadros_vectores(primero, segundo):
        escalado = [a_flotante_seguro(valor) for valor in cuadro.vector_escalado]
        suma = [a_flotante_seguro(valor) for valor in cuadro.suma]
        cuadros.append({
            "escalar": float(cuadro.escalar), "escalar_exacto": str(cuadro.escalar),
            "escalar_por_u": escalado, "escalar_por_u_mas_v": suma,
        })
        valores.extend(valor for valor in escalado if valor is not None)
        valores.extend(valor for valor in suma if valor is not None)
    return cuadros, valores
