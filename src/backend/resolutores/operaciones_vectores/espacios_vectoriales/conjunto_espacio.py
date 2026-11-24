"""Caracterización exacta del conjunto de vectores y pruebas de pertenencia."""
from dataclasses import dataclass
from fractions import Fraction

from src.backend.constantes import EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.reduccion.reduccion import ReductorFilas
from ..subespacios.comprobacion_subespacios import CONFIGURACION_EXACTA
from ..subespacios.contrato_subespacios import EntradaSubespacio
from ..subespacios.subespacios import analizar_subespacio
from .contrato_espacio_vectorial import VectorExacto
from .limites_espacio_vectorial import (
    MAXIMO_BITS_CALCULO, LimiteAritmeticoEspacio, racional_admitido,
)
from .polinomios_espacio import AritmeticaPolinomica, Polinomio, VectorPolinomico


class ErrorCaracterizacionEspacio(ArithmeticError):
    """Indica que falló la caracterización exacta del conjunto."""


@dataclass(frozen=True)
class FamiliaAfin:
    """Representa particular, direcciones independientes y ecuaciones de pertenencia."""

    particular: VectorExacto
    direcciones: tuple[VectorExacto, ...]
    restricciones: tuple[VectorExacto, ...]

    def parametrizar(
        self, algebra: AritmeticaPolinomica, parametros: VectorPolinomico,
    ) -> VectorPolinomico:
        """Devuelve el punto formal p + B·t para los parámetros indicados."""
        return tuple(
            algebra.combinar((valor, *factores), (algebra.constante(Fraction(1)), *parametros))
            for valor, factores in zip(self.particular, self._filas_direcciones(), strict=True)
        )

    def pertenencia(
        self, algebra: AritmeticaPolinomica, vector: VectorPolinomico,
    ) -> VectorPolinomico:
        """Devuelve los residuos de las restricciones lineales aplicadas al vector."""
        uno = algebra.constante(Fraction(1))
        return tuple(algebra.combinar(fila, (*vector, uno)) for fila in self.restricciones)

    def _filas_direcciones(self) -> tuple[VectorExacto, ...]:
        if not self.direcciones:
            return ((),) * len(self.particular)
        return tuple(zip(*self.direcciones, strict=True))


def caracterizar_conjunto(entrada: EntradaSubespacio) -> FamiliaAfin | None:
    """Reusa el análisis exacto y devuelve la familia afín, o None si el conjunto es vacío."""
    resultado = analizar_subespacio(entrada)
    if resultado["estado"] != EXITO:
        raise ErrorCaracterizacionEspacio("No se pudo caracterizar el conjunto.")
    if resultado["es_vacio"]:
        return None
    if entrada["modo"] == "generadores":
        base = resultado["base"]
        if base is None:
            raise ErrorCaracterizacionEspacio("La caracterización omitió la base.")
        familia = _familia_generada(base, entrada["dimension_ambiente"])
    else:
        particular, direcciones = resultado["particular"], resultado["direcciones"]
        if particular is None or direcciones is None:
            raise ErrorCaracterizacionEspacio("La caracterización omitió la familia afín.")
        restricciones = tuple(
            (*map(Fraction, fila), -termino)
            for fila, termino in zip(entrada["matriz_a"].datos, entrada["vector_b"], strict=True)
        )
        familia = FamiliaAfin(particular, direcciones, restricciones)
    _validar_familia(familia)
    return familia


def _familia_generada(base: tuple[VectorExacto, ...], dimension: int) -> FamiliaAfin:
    particular = (Fraction(0),) * dimension
    if len(base) == dimension:
        return FamiliaAfin(particular, base, ())
    if not base:
        return FamiliaAfin(particular, base, tuple(_ecuacion_libre(indice, dimension, {}) for indice in range(dimension)))
    matriz = Matriz(len(base), dimension, [list(vector) for vector in base])
    reduccion = ReductorFilas(matriz, dimension, CONFIGURACION_EXACTA).reducir()
    filas = dict(zip(reduccion["columnas_pivote"], reduccion["matriz_reducida"].datos, strict=True))
    restricciones = tuple(
        _ecuacion_libre(indice, dimension, filas) for indice in range(dimension) if indice not in filas
    )
    return FamiliaAfin(particular, base, restricciones)


def _ecuacion_libre(indice: int, dimension: int, filas: dict[int, list]) -> VectorExacto:
    coeficientes = [Fraction(0)] * (dimension + 1)
    coeficientes[indice] = Fraction(1)
    for pivote, fila in filas.items():
        coeficientes[pivote] = -Fraction(fila[indice])
    return tuple(coeficientes)


def _validar_familia(familia: FamiliaAfin) -> None:
    filas = (familia.particular, *familia.direcciones, *familia.restricciones)
    if any(not racional_admitido(valor, MAXIMO_BITS_CALCULO) for fila in filas for valor in fila):
        raise LimiteAritmeticoEspacio("La caracterización excedió el tamaño máximo de cálculo.")
