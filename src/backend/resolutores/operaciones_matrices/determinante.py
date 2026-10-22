"""Determinantes exactos por Laplace o eliminacion con pivoteo parcial."""
from fractions import Fraction
from typing import Any

from src.backend.constantes import DIMENSION_MAXIMA_COFACTORES
from src.backend.modelos.matriz import Matriz
from .cofactores import ExpansionCofactores, describir_limites_cofactores, seleccionar_fila
from .calculo_determinante import triangular_y_determinante
from .pasos_determinante import RegistroPasosDeterminante
from .traza_cofactores import construir_traza_cofactores


class ResolutorDeterminante:
    """Ofrece ambos metodos sin reemplazar una eleccion explicita por la recomendacion."""

    @classmethod
    def recomendar_metodo(cls, datos: list[list[Any]]) -> dict[str, Any]:
        """Sugiere metodo segun orden y ceros de las filas; ValueError ante datos invalidos."""
        matriz = Matriz(len(datos), len(datos), datos)
        dimension = matriz.filas
        fila = seleccionar_fila(matriz.datos)
        ceros = matriz.datos[fila].count(0)
        laplace = dimension <= DIMENSION_MAXIMA_COFACTORES and (dimension <= 2 or ceros >= dimension - 1)
        return {
            "metodo_recomendado": "laplace" if laplace else "lu",
            "nombre_legible": "Cofactores (Laplace)" if laplace else "Eliminacion con pivoteo",
            "justificacion": (
                f"Orden {dimension}: la fila {fila + 1} tiene {ceros} ceros. "
                "Laplace cuesta O(n!) en el peor caso; eliminacion cuesta O(n^3). "
                "La recomendacion no cambia tu eleccion."
            ),
            "cofactores_disponibles": dimension <= DIMENSION_MAXIMA_COFACTORES,
            "limites_cofactores": describir_limites_cofactores(),
        }

    @classmethod
    def _determinante_recursivo(cls, datos: list[list[Fraction]]) -> Fraction:
        """Delega el acceso historico al motor acotado de cofactores."""
        matriz = Matriz(len(datos), len(datos), datos)
        return ExpansionCofactores().calcular(matriz)["determinante"]

    @classmethod
    def resolver_laplace(cls, matriz: Matriz) -> dict[str, Any]:
        """Devuelve valor y traza exactos; ValueError ante forma o coste no admitidos."""
        expansion = ExpansionCofactores().calcular(matriz)
        traza = construir_traza_cofactores(matriz, expansion)
        valor = expansion["determinante"]
        return {"metodo": "laplace", "determinante": valor, "es_singular": valor == 0,
                "pasos": [paso["descripcion"] for paso in traza], "traza": traza,
                "fila_elegida": expansion["fila"], "nodos": expansion["nodos"],
                "limites_cofactores": describir_limites_cofactores()}

    @classmethod
    def resolver_lu(cls, matriz: Matriz) -> dict[str, Any]:
        """Triangulariza con pivoteo parcial; conserva el nombre interno lu por compatibilidad."""
        if matriz.filas != matriz.columnas:
            raise ValueError("El determinante requiere una matriz cuadrada.")
        registro = RegistroPasosDeterminante()
        determinante, reduccion = triangular_y_determinante(matriz, registro.registrar, "parcial")
        registro.cerrar(reduccion, determinante)
        return {"metodo": "lu", "determinante": determinante, "es_singular": determinante == 0,
                "pasos": registro.pasos, "traza": registro.traza,
                "intercambios": reduccion["intercambios"]}
