"""Orquestacion del modelo de insumo-producto sin calculo ni formato duplicados."""
from fractions import Fraction

from src.backend.constantes import ERROR
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.calculo_leontief import calcular_leontief
from src.backend.resolutores.operaciones_matrices.presentacion_leontief import presentar_leontief


class ResolutorModeloLeontief:
    """Valida dimensiones, delega el balance exacto y presenta su resultado economico."""

    def resolver(self, matriz_coeficientes: Matriz, vector_demanda: list[Fraction],
                 nombres_sectores: list[str] | None = None) -> dict:
        """Devuelve produccion, matrices y analisis para coeficientes y demanda, o error de dimensiones."""
        if matriz_coeficientes.filas != matriz_coeficientes.columnas:
            return {"estado": ERROR, "mensaje": "La matriz de coeficientes debe ser cuadrada (n×n)."}
        dimension = matriz_coeficientes.filas
        if len(vector_demanda) != dimension:
            return {"estado": ERROR, "mensaje": f"El vector de demanda debe tener {dimension} componentes; se recibieron {len(vector_demanda)}."}
        sectores = (nombres_sectores if nombres_sectores and len(nombres_sectores) == dimension
                    else [f"Sector {indice + 1}" for indice in range(dimension)])
        return presentar_leontief(calcular_leontief(matriz_coeficientes, vector_demanda), vector_demanda, sectores)
