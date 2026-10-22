"""Sustitucion regresiva pura y base canonica del espacio nulo."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.modelo_solucion import ParametrosSolucion, validar_invariantes_parametricos


def _despejar_valor(fila: list, columna: int, vector: list[Fraction], termino: Fraction) -> Fraction:
    acumulado = sum(Fraction(coeficiente) * valor
                    for coeficiente, valor in zip(fila[columna + 1:len(vector)], vector[columna + 1:]))
    return (termino - acumulado) / Fraction(fila[columna])


def calcular_solucion_parametrica(matriz: Matriz, columnas_pivote: list[int], numero_variables: int) -> ParametrosSolucion:
    """Devuelve particular y direcciones exactas desde la matriz escalonada y sus columnas pivote."""
    libres = [columna for columna in range(numero_variables) if columna not in columnas_pivote]
    particular = [Fraction(0)] * numero_variables
    direcciones = [[Fraction(0)] * numero_variables for _ in libres]
    for indice, columna in enumerate(libres):
        direcciones[indice][columna] = Fraction(1)
    for fila_indice in range(len(columnas_pivote) - 1, -1, -1):
        columna = columnas_pivote[fila_indice]
        fila = matriz.datos[fila_indice]
        particular[columna] = _despejar_valor(fila, columna, particular, Fraction(fila[numero_variables]))
        for direccion in direcciones:
            direccion[columna] = _despejar_valor(fila, columna, direccion, Fraction(0))
    validar_invariantes_parametricos(direcciones, particular, libres)
    return {"numero_variables": numero_variables, "columnas_libres": libres,
            "particular": particular, "direcciones": direcciones}
