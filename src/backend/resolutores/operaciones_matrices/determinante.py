"""Resolutor de determinantes mediante expansion por cofactores (Laplace) y LU."""

from fractions import Fraction
from typing import Any

from src.backend.modelos.matriz import Matriz


class ResolutorDeterminante:
    """Calcula determinantes por cofactores o triangulacion LU con recomendaciones."""

    @classmethod
    def recomendar_metodo(cls, datos: list[list[Any]]) -> dict[str, Any]:
        """Sugiere Laplace o LU según el tamaño y dispersión de la matriz recibida."""
        dimension = len(datos)
        if dimension <= 2:
            return {
                "metodo_recomendado": "laplace",
                "nombre_legible": "Expansion por Cofactores (Directo)",
                "justificacion": f"Para matrices de orden {dimension}x{dimension}, la formula directa de cofactores es optima e inmediata.",
            }

        max_ceros = max(sum(1 for valor in fila if Fraction(valor) == 0) for fila in datos)
        for j in range(dimension):
            columna_ceros = sum(1 for i in range(dimension) if Fraction(datos[i][j]) == 0)
            max_ceros = max(max_ceros, columna_ceros)

        if max_ceros >= dimension - 1:
            return {
                "metodo_recomendado": "laplace",
                "nombre_legible": "Expansion por Cofactores (Laplace)",
                "justificacion": f"Existe una linea con {max_ceros} ceros. Laplace reduce drasticamente el numero de subdeterminantes.",
            }

        return {
            "metodo_recomendado": "lu",
            "nombre_legible": "Triangulacion Gaussiana / LU",
            "justificacion": f"Para orden {dimension}x{dimension} denso, la triangulacion tiene complejidad polinomica O(n^3) frente a O(n!) de cofactores.",
        }

    @staticmethod
    def _seleccionar_mejor_fila_ceros(m_datos: list[list[Fraction]]) -> int:
        """Encuentra la fila con mayor cantidad de ceros para expansion de Laplace."""
        mejor_fila = 0
        max_ceros = -1
        for i, fila in enumerate(m_datos):
            ceros = sum(1 for valor in fila if valor == 0)
            if ceros > max_ceros:
                max_ceros = ceros
                mejor_fila = i
        return mejor_fila

    @classmethod
    def _det_recursivo(cls, m_datos: list[list[Fraction]]) -> Fraction:
        """Calcula el determinante por cofactores de manera recursiva."""
        orden = len(m_datos)
        if orden == 1:
            return m_datos[0][0]
        if orden == 2:
            return m_datos[0][0] * m_datos[1][1] - m_datos[0][1] * m_datos[1][0]

        mejor_fila = cls._seleccionar_mejor_fila_ceros(m_datos)
        determinante_acumulado = Fraction(0)
        for j in range(orden):
            elem = m_datos[mejor_fila][j]
            if elem == 0:
                continue
            signo = (-1) ** (mejor_fila + j)
            sub_matriz = [
                [m_datos[r][c] for c in range(orden) if c != j]
                for r in range(orden) if r != mejor_fila
            ]
            determinante_acumulado += Fraction(signo) * elem * cls._det_recursivo(sub_matriz)
        return determinante_acumulado

    @classmethod
    def resolver_laplace(cls, matriz: Matriz) -> dict[str, Any]:
        """Calcula el determinante aplicando expansion por cofactores de Laplace."""
        if matriz.filas != matriz.columnas:
            raise ValueError("El determinante requiere una matriz cuadrada.")

        datos = [[matriz.obtener(i, j) for j in range(matriz.columnas)] for i in range(matriz.filas)]
        determinante_final = cls._det_recursivo(datos)
        return {
            "metodo": "laplace",
            "determinante": determinante_final,
            "es_singular": determinante_final == 0,
            "pasos": [f"Determinante calculado por cofactores: {determinante_final}"],
        }

    @staticmethod
    def _buscar_pivote_no_nulo(copia: list[list[Fraction]], columna: int, dimension: int) -> int:
        """Encuentra el índice de la primera fila con pivote no nulo."""
        pivote_fila = columna
        while pivote_fila < dimension and copia[pivote_fila][columna] == 0:
            pivote_fila += 1
        return pivote_fila

    @staticmethod
    def _restar_multiplo_fila(
        copia: list[list[Fraction]],
        f: int,
        columna: int,
        factor: Fraction,
    ) -> None:
        """Resta factor * copia[col] a copia[f] desde la columna col."""
        dimension = len(copia)
        for c_indice in range(columna, dimension):
            copia[f][c_indice] -= factor * copia[columna][c_indice]

    @classmethod
    def _triangular(cls, copia: list[list[Fraction]], dimension: int) -> tuple[int, list[str], bool]:
        """Reduce la matriz a triangular superior registrando intercambios y operaciones."""
        signo = 1
        pasos = []
        for columna in range(dimension):
            pivote_fila = cls._buscar_pivote_no_nulo(copia, columna, dimension)
            if pivote_fila == dimension:
                return 0, ["Se encontro un pivote nulo sin posibilidad de intercambio. La matriz es singular (det = 0)."], True

            if pivote_fila != columna:
                copia[columna], copia[pivote_fila] = copia[pivote_fila], copia[columna]
                signo *= -1
                pasos.append(f"Intercambio de Fila {columna + 1} con Fila {pivote_fila + 1}")

            pivote = copia[columna][columna]
            for f in range(columna + 1, dimension):
                factor = copia[f][columna] / pivote
                if factor != 0:
                    cls._restar_multiplo_fila(copia, f, columna, factor)
                    pasos.append(f"Fila {f + 1} = Fila {f + 1} - ({factor}) * Fila {columna + 1}")
        return signo, pasos, False

    @classmethod
    def resolver_lu(cls, matriz: Matriz) -> dict[str, Any]:
        """Calcula el determinante reduciendo la matriz a forma triangular."""
        dimension = matriz.filas
        if dimension != matriz.columnas:
            raise ValueError("El determinante requiere una matriz cuadrada.")

        copia = [[Fraction(matriz.obtener(i, j)) for j in range(dimension)] for i in range(dimension)]
        signo, pasos, es_singular = cls._triangular(copia, dimension)
        if es_singular:
            return {
                "metodo": "lu",
                "determinante": Fraction(0),
                "es_singular": True,
                "pasos": pasos,
            }

        determinante = Fraction(signo)
        for i in range(dimension):
            determinante *= copia[i][i]

        return {
            "metodo": "lu",
            "determinante": determinante,
            "es_singular": determinante == 0,
            "pasos": pasos + [f"Producto diagonal * signo = {determinante}"],
        }
