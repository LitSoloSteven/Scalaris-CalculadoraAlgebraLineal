"""Inversion pura sobre el motor compartido de Gauss-Jordan."""
from collections.abc import Callable

from src.backend.modelos.construcciones import aumentar_con_identidad
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.calculo_determinante import triangular_y_determinante
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas


def calcular_inversa(matriz: Matriz, registrar: Callable | None = None, registrar_determinante: Callable | None = None) -> dict:
    """Devuelve determinante, aumentada, rango e inversa opcional de matriz cuadrada sin formatear."""
    dimension = matriz.filas
    determinante, _ = triangular_y_determinante(matriz, registrar_determinante)
    if determinante == 0:
        return {"determinante": determinante, "inversa": None, "aumentada": None, "rango": None}
    aumentada = aumentar_con_identidad(matriz)
    opciones = ConfiguracionReduccion(reduccion_completa=True)
    resultado = ReductorFilas(aumentada, dimension, opciones, registrar).reducir()
    reducida = resultado["matriz_reducida"]
    inversa = None
    if resultado["rango"] == dimension:
        inversa = Matriz(dimension, dimension, [fila[dimension:] for fila in reducida.datos])
    return {"determinante": determinante, "inversa": inversa,
            "aumentada": aumentada, "rango": resultado["rango"]}
