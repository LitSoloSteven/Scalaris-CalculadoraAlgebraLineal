"""Expansion exacta de Laplace con presupuesto compartido para todos los menores."""
from fractions import Fraction

from src.backend.constantes import DIMENSION_MAXIMA_COFACTORES
from src.backend.modelos.matriz import Matriz

MAXIMO_NODOS_COFACTORES = 10000


def describir_limites_cofactores() -> str:
    """Devuelve los limites de dimension y trabajo aplicados por el motor."""
    return (
        f"La expansion por cofactores admite hasta {DIMENSION_MAXIMA_COFACTORES} filas y "
        f"{MAXIMO_NODOS_COFACTORES} subproblemas. Su coste es O(n!) en matrices "
        "densas; los ceros reducen el trabajo recursivo. Si se supera el limite, "
        "elige eliminacion con pivoteo. No se cambia de metodo automaticamente."
    )


def seleccionar_fila(datos: list[list[Fraction]]) -> int:
    """Devuelve el indice local de la primera fila con mas ceros."""
    return max(range(len(datos)), key=lambda indice: datos[indice].count(0))


def construir_menor(datos: list[list[Fraction]], fila: int, columna: int) -> list[list[Fraction]]:
    """Elimina fila y columna locales conservando el orden de los demas indices."""
    return [[valor for indice, valor in enumerate(valores) if indice != columna]
            for posicion, valores in enumerate(datos) if posicion != fila]


class ExpansionCofactores:
    """Calcula una expansion y contabiliza su trabajo antes de cada subproblema."""

    def __init__(self) -> None:
        """Inicializa un presupuesto independiente por solicitud."""
        self.nodos = 0

    def _valor(self, datos: list[list[Fraction]]) -> Fraction:
        self.nodos += 1
        if self.nodos > MAXIMO_NODOS_COFACTORES:
            raise ValueError("Se supero el presupuesto de cofactores. " + describir_limites_cofactores())
        if len(datos) == 1:
            return datos[0][0]
        if len(datos) == 2:
            return datos[0][0] * datos[1][1] - datos[0][1] * datos[1][0]
        fila = seleccionar_fila(datos)
        return sum(((-1) ** (fila + columna) * elemento
                    * self._valor(construir_menor(datos, fila, columna))
                    for columna, elemento in enumerate(datos[fila]) if elemento != 0), Fraction(0))

    def calcular(self, matriz: Matriz) -> dict:
        """Devuelve fila, menores, valores exactos y coste; lanza ValueError al exceder limites."""
        if matriz.filas != matriz.columnas:
            raise ValueError("El determinante requiere una matriz cuadrada.")
        if matriz.filas > DIMENSION_MAXIMA_COFACTORES:
            raise ValueError(describir_limites_cofactores())
        datos = [[Fraction(valor) for valor in fila] for fila in matriz.datos]
        fila = seleccionar_fila(datos)
        if matriz.filas == 1:
            return {"fila": 1, "menores": [], "determinante": self._valor(datos), "nodos": self.nodos}
        menores = []
        acumulado = Fraction(0)
        for columna, elemento in enumerate(datos[fila]):
            menor = self._calcular_menor(datos, (fila, columna), elemento)
            acumulado += menor["termino"]
            menores.append({**menor, "acumulado": acumulado})
        return {"fila": fila + 1, "menores": menores, "determinante": acumulado, "nodos": self.nodos}

    def _calcular_menor(self, datos: list, coordenadas: tuple[int, int], elemento: Fraction) -> dict:
        fila, columna = coordenadas
        menor = construir_menor(datos, fila, columna)
        valor = self._valor(menor)
        signo = (-1) ** (fila + columna)
        cofactor = signo * valor
        return {
            "fila": fila + 1, "columna": columna + 1, "elemento": elemento,
            "matriz_menor": Matriz(len(menor), len(menor), menor),
            "filas_originales": [indice + 1 for indice in range(len(datos)) if indice != fila],
            "columnas_originales": [indice + 1 for indice in range(len(datos)) if indice != columna],
            "valor_menor": valor, "signo": signo, "cofactor": cofactor, "termino": elemento * cofactor,
        }
