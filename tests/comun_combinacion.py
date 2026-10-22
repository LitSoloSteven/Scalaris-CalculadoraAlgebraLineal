"""Preparación del ejemplo canónico de combinación lineal de Lay."""
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal


def preparar_combinacion_canonica():
    """Devuelve resolutor, generadores, objetivo y resultado con los mismos nombres simbólicos."""
    primero = Matriz(3, 1, [[1], [-2], [-5]])
    segundo = Matriz(3, 1, [[2], [5], [6]])
    objetivo = Matriz(3, 1, [[7], [4], [-3]])
    resolutor = ResolutorCombinacionLineal()
    resultado = resolutor.resolver(objetivo, [primero, segundo],
                                  nombres_variables=['x_1', 'x_2'], nombres_vectores=['a_1', 'a_2'])
    return resolutor, primero, segundo, objetivo, resultado
