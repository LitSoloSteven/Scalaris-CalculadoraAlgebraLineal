"""Analisis de transformaciones con reduccion y parametrizacion compartidas."""
from src.backend.constantes import CERO_EPSILON, ERROR
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.presentacion_transformaciones import presentar_transformacion
from src.backend.resolutores.sistemas_lineales.calculo_solucion import calcular_solucion_parametrica
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan
from .aplicacion_transformacion import aplicar_vector


class ResolutorTransformacionesLineales:
    """Orquesta el analisis de nucleo e imagen sin repetir la construccion de direcciones nulas."""

    def __init__(self, tolerancia_cero: float = CERO_EPSILON) -> None:
        """Recibe la tolerancia para entradas flotantes; los racionales se comparan exactamente."""
        self.tolerancia_cero = tolerancia_cero

    def resolver(self, matriz_a: Matriz, nombres_variables: list[str] | None = None) -> dict:
        """Devuelve analisis, bases y pasos de matriz_a con etiquetas opcionales, o estado ERROR."""
        if not isinstance(matriz_a, Matriz):
            return {"estado": ERROR, "mensaje": "Se esperaba una instancia de Matriz."}
        nombres = (nombres_variables if nombres_variables and len(nombres_variables) == matriz_a.columnas
                   else [f"x_{{{indice+1}}}" for indice in range(matriz_a.columnas)])
        aumentada = Matriz(matriz_a.filas, matriz_a.columnas + 1, [fila + [0] for fila in matriz_a.datos])
        reduccion = ResolutorGaussJordan(aumentada, self.tolerancia_cero, nombres).resolver_reduccion()
        parametros = calcular_solucion_parametrica(reduccion["matriz_reducida"], reduccion["columnas_pivote"], matriz_a.columnas)
        return presentar_transformacion(matriz_a, reduccion, parametros, nombres)
    
    def aplicar(self, matriz: Matriz, vector: Matriz) -> dict:
        """Delega el cálculo exacto de T(v) = A·v al módulo de aplicación."""
        return aplicar_vector(matriz, vector)
