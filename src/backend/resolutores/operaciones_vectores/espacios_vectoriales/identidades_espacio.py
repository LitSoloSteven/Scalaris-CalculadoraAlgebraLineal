"""Construye los residuos de los axiomas sobre parámetros reales independientes."""
from fractions import Fraction

from .conjunto_espacio import FamiliaAfin
from .contrato_espacio_vectorial import AxiomaEspacioVectorial, EntradaEspacioVectorial, VectorExacto
from .polinomios_espacio import (
    AritmeticaPolinomica, Polinomio, PresupuestoPolinomico, VectorPolinomico,
)

_PARAMETROS: dict[AxiomaEspacioVectorial, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "CIERRE_SUMA": (("u", "v"), ()),
    "CIERRE_ESCALAR": (("u",), ("alfa",)),
    "CONMUTATIVIDAD_SUMA": (("u", "v"), ()),
    "ASOCIATIVIDAD_SUMA": (("u", "v", "w"), ()),
    "NEUTRO_SUMA": (("u",), ()),
    "INVERSO_SUMA": (("u",), ()),
    "IDENTIDAD_ESCALAR": (("u",), ()),
    "ASOCIATIVIDAD_ESCALAR": (("u",), ("alfa", "beta")),
    "DISTRIBUTIVIDAD_VECTORES": (("u", "v"), ("alfa",)),
    "DISTRIBUTIVIDAD_ESCALARES": (("u",), ("alfa", "beta")),
}
_UNO = Fraction(1)
_MENOS_UNO = -_UNO


class IdentidadesEspacio:
    """Evalúa identidades con las operaciones de la entrada y una familia afín exacta."""

    def __init__(self, entrada: EntradaEspacioVectorial, familia: FamiliaAfin) -> None:
        """Conserva las operaciones y abre un presupuesto para todos los axiomas."""
        self._entrada = entrada
        self._familia = familia
        self._presupuesto = PresupuestoPolinomico()

    def candidato_neutro(self) -> VectorExacto:
        """Calcula el candidato 0 ⊙ p evaluando únicamente constantes exactas."""
        algebra = AritmeticaPolinomica(0, self._presupuesto)
        punto = algebra.vector_constante(self._familia.particular)
        candidato = algebra.componer(self._entrada["producto_escalar"], ({}, *punto))
        return tuple(coordenada.get((), Fraction(0)) for coordenada in candidato)

    def residuos(
        self, axioma: AxiomaEspacioVectorial, neutro: VectorExacto | None = None,
    ) -> tuple[tuple[str, ...], VectorPolinomico]:
        """Devuelve nombres de variables y residuos exactos, o propaga el límite aritmético."""
        vectores, escalares = _PARAMETROS[axioma]
        cantidad = len(self._familia.direcciones)
        nombres = tuple(f"{nombre}{indice}" for nombre in vectores for indice in range(1, cantidad + 1))
        variables = (*nombres, *escalares)
        algebra = AritmeticaPolinomica(len(variables), self._presupuesto)
        operandos = tuple(algebra.variable(indice) for indice in range(len(variables)))
        puntos = tuple(
            self._familia.parametrizar(algebra, operandos[inicio:inicio + cantidad])
            for inicio in (indice * cantidad for indice in range(len(vectores)))
        )
        entorno = _EntornoIdentidades(self._entrada, self._familia, algebra)
        if neutro is not None:
            resultado = entorno.aditivos(axioma, puntos[0], algebra.vector_constante(neutro))
        else:
            resultado = entorno.directos(axioma, puntos, operandos[len(nombres):])
        return variables, resultado


class _EntornoIdentidades:
    def __init__(self, entrada: EntradaEspacioVectorial, familia: FamiliaAfin, algebra: AritmeticaPolinomica):
        self._entrada = entrada
        self._familia = familia
        self._algebra = algebra

    def directos(
        self, axioma: AxiomaEspacioVectorial, puntos: tuple[VectorPolinomico, ...], escalares: VectorPolinomico,
    ) -> VectorPolinomico:
        """Evalúa un axioma que no depende de haber determinado el neutro."""
        primero = puntos[0]
        if axioma == "CIERRE_SUMA":
            return self._familia.pertenencia(self._algebra, self._sumar(*puntos))
        if axioma == "CIERRE_ESCALAR":
            return self._familia.pertenencia(self._algebra, self._escalar(escalares[0], primero))
        if axioma == "CONMUTATIVIDAD_SUMA":
            return self._diferencia(self._sumar(*puntos), self._sumar(*reversed(puntos)))
        if axioma == "ASOCIATIVIDAD_SUMA":
            _, segundo, tercero = puntos
            return self._diferencia(
                self._sumar(self._sumar(primero, segundo), tercero),
                self._sumar(primero, self._sumar(segundo, tercero)),
            )
        return self._identidades_escalares(axioma, puntos, escalares)

    def aditivos(
        self, axioma: AxiomaEspacioVectorial, vector: VectorPolinomico, neutro: VectorPolinomico,
    ) -> VectorPolinomico:
        """Comprueba pertenencia e identidades bilaterales de los candidatos aditivos."""
        if axioma == "NEUTRO_SUMA":
            return (*self._familia.pertenencia(self._algebra, neutro), *self._bilateral(vector, neutro, vector))
        inverso = self._escalar(self._algebra.constante(_MENOS_UNO), vector)
        return (*self._familia.pertenencia(self._algebra, inverso), *self._bilateral(vector, inverso, neutro))

    def _identidades_escalares(
        self, axioma: AxiomaEspacioVectorial, puntos: tuple[VectorPolinomico, ...], escalares: VectorPolinomico,
    ) -> VectorPolinomico:
        primero = puntos[0]
        if axioma == "IDENTIDAD_ESCALAR":
            return self._diferencia(self._escalar(self._algebra.constante(_UNO), primero), primero)
        alfa = escalares[0]
        producto = self._escalar(alfa, primero)
        if axioma == "DISTRIBUTIVIDAD_VECTORES":
            return self._diferencia(
                self._escalar(alfa, self._sumar(*puntos)), self._sumar(producto, self._escalar(alfa, puntos[1]))
            )
        beta = escalares[1]
        producto_beta = self._escalar(beta, primero)
        if axioma == "ASOCIATIVIDAD_ESCALAR":
            multiplicado = self._producto_escalar_formal(alfa, beta)
            return self._diferencia(self._escalar(multiplicado, primero), self._escalar(alfa, producto_beta))
        suma = self._algebra.combinar((_UNO, _UNO), (alfa, beta))
        return self._diferencia(self._escalar(suma, primero), self._sumar(producto, producto_beta))

    def _producto_escalar_formal(self, alfa: Polinomio, beta: Polinomio) -> Polinomio:
        return self._algebra.componer(_PRODUCTO_REAL, (alfa, beta))[0]

    def _sumar(self, primero: VectorPolinomico, segundo: VectorPolinomico) -> VectorPolinomico:
        return self._algebra.componer(self._entrada["suma"], (*primero, *segundo))

    def _escalar(self, escalar: Polinomio, vector: VectorPolinomico) -> VectorPolinomico:
        return self._algebra.componer(self._entrada["producto_escalar"], (escalar, *vector))

    def _diferencia(self, primero: VectorPolinomico, segundo: VectorPolinomico) -> VectorPolinomico:
        return tuple(
            self._algebra.combinar((_UNO, _MENOS_UNO), (izquierdo, derecho))
            for izquierdo, derecho in zip(primero, segundo, strict=True)
        )

    def _bilateral(
        self, primero: VectorPolinomico, segundo: VectorPolinomico, esperado: VectorPolinomico,
    ) -> VectorPolinomico:
        return (*self._diferencia(self._sumar(primero, segundo), esperado),
                *self._diferencia(self._sumar(segundo, primero), esperado))


_PRODUCTO_REAL = (({"coeficiente": _UNO, "exponentes": (1, 1)},),)
