"""Controles comunes de suma vectorial con ajuste de orientación."""
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores


def comprobar_suma_columna(primero, segundo):
    """Exige resultado exacto [5, 7, 9] de tres filas y una columna."""
    resultado = ResolutorOperacionesVectores().sumar(primero, segundo)
    assert resultado['estado'] == 'EXITO'
    assert resultado['matriz_resultado'].datos == [[5], [7], [9]]
    assert resultado['matriz_resultado'].filas == 3
    assert resultado['matriz_resultado'].columnas == 1
    return resultado
