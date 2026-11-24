"""Aritmética dispersa sobre racionales con un presupuesto compartido por análisis."""
from fractions import Fraction

from . import limites_espacio_vectorial as limites
from .contrato_espacio_vectorial import OperacionPolinomica, TerminoPolinomico, VectorExacto

Exponentes = tuple[int, ...]
Polinomio = dict[Exponentes, Fraction]
VectorPolinomico = tuple[Polinomio, ...]


class PresupuestoPolinomico:
    """Cuenta el trabajo disperso realizado durante una solicitud."""

    def __init__(self) -> None:
        """Inicia el contador con la cota de operaciones configurada."""
        self.restantes = limites.MAXIMO_OPERACIONES

    def consumir(self) -> None:
        """Descuenta una operación y lanza el límite si se agotó el presupuesto."""
        if self.restantes <= 0:
            raise limites.LimiteAritmeticoEspacio("Se agotó el presupuesto de operaciones exactas.")
        self.restantes -= 1


class AritmeticaPolinomica:
    """Expande polinomios en una lista fija de variables independientes."""

    def __init__(self, cantidad_variables: int, presupuesto: PresupuestoPolinomico) -> None:
        """Fija el orden de exponentes y reutiliza el presupuesto de la solicitud."""
        self._exponentes_cero = (0,) * cantidad_variables
        self._presupuesto = presupuesto

    def constante(self, valor: Fraction) -> Polinomio:
        """Devuelve la constante exacta o lanza el límite si el racional es demasiado grande."""
        _validar_racional(valor)
        return {self._exponentes_cero: valor} if valor else {}

    def vector_constante(self, vector: VectorExacto) -> VectorPolinomico:
        """Convierte cada coordenada racional en un polinomio constante."""
        return tuple(self.constante(valor) for valor in vector)

    def variable(self, indice: int) -> Polinomio:
        """Devuelve la variable en la posición dada, que empieza en cero."""
        exponentes = list(self._exponentes_cero)
        exponentes[indice] = 1
        return {tuple(exponentes): Fraction(1)}

    def combinar(self, factores: VectorExacto, polinomios: VectorPolinomico) -> Polinomio:
        """Devuelve una combinación lineal exacta dentro de los límites de expansión."""
        resultado: Polinomio = {}
        for factor, polinomio in zip(factores, polinomios, strict=True):
            self._acumular_polinomio(resultado, factor, polinomio)
        return resultado

    def componer(self, operacion: OperacionPolinomica, operandos: VectorPolinomico) -> VectorPolinomico:
        """Sustituye los operandos en las coordenadas y devuelve sus expansiones exactas."""
        potencias: dict[tuple[int, int], Polinomio] = {}
        return tuple(self._componer_coordenada(terminos, operandos, potencias) for terminos in operacion)

    def _componer_coordenada(
        self, terminos: tuple[TerminoPolinomico, ...], operandos: VectorPolinomico,
        potencias: dict[tuple[int, int], Polinomio],
    ) -> Polinomio:
        resultado: Polinomio = {}
        for termino in terminos:
            self._presupuesto.consumir()
            producto = self.constante(termino["coeficiente"])
            for indice, exponente in enumerate(termino["exponentes"]):
                if not producto:
                    break
                if exponente:
                    potencia = self._potencia(operandos, (indice, exponente), potencias)
                    producto = self._multiplicar(producto, potencia)
            self._acumular_polinomio(resultado, Fraction(1), producto)
        return resultado

    def _potencia(
        self, operandos: VectorPolinomico, clave: tuple[int, int],
        potencias: dict[tuple[int, int], Polinomio],
    ) -> Polinomio:
        if clave in potencias:
            return potencias[clave]
        indice, exponente = clave
        if exponente == 1:
            return operandos[indice]
        mitad = self._potencia(operandos, (indice, exponente // 2), potencias)
        potencia = self._multiplicar(mitad, mitad)
        if exponente % 2:
            potencia = self._multiplicar(potencia, operandos[indice])
        potencias[clave] = potencia
        return potencia

    def _multiplicar(self, izquierdo: Polinomio, derecho: Polinomio) -> Polinomio:
        resultado: Polinomio = {}
        for exponentes, coeficiente in izquierdo.items():
            for otros_exponentes, otro_coeficiente in derecho.items():
                grados = tuple(map(int.__add__, exponentes, otros_exponentes))
                if sum(grados) > limites.MAXIMO_GRADO_CALCULO:
                    raise limites.LimiteAritmeticoEspacio("La expansión excedió el grado máximo.")
                self._acumular_termino(resultado, grados, coeficiente * otro_coeficiente)
        return resultado

    def _acumular_polinomio(self, resultado: Polinomio, factor: Fraction, fuente: Polinomio) -> None:
        if factor:
            for exponentes, coeficiente in fuente.items():
                self._acumular_termino(resultado, exponentes, factor * coeficiente)

    def _acumular_termino(self, resultado: Polinomio, exponentes: Exponentes, valor: Fraction) -> None:
        self._presupuesto.consumir()
        _validar_racional(valor)
        if exponentes in resultado:
            valor += resultado[exponentes]
            _validar_racional(valor)
        if valor:
            resultado[exponentes] = valor
            if len(resultado) > limites.MAXIMO_TERMINOS_CALCULO:
                raise limites.LimiteAritmeticoEspacio("La expansión excedió la cantidad máxima de términos.")
        else:
            resultado.pop(exponentes, None)


def _validar_racional(valor: Fraction) -> None:
    if not limites.racional_admitido(valor, limites.MAXIMO_BITS_CALCULO):
        raise limites.LimiteAritmeticoEspacio("Un racional excedió el tamaño máximo de cálculo.")


def normalizar_residuos(residuos: VectorPolinomico) -> OperacionPolinomica:
    """Serializa coeficientes no nulos, con exponentes en orden lexicográfico."""
    return tuple(
        tuple({"coeficiente": valor, "exponentes": exponentes} for exponentes, valor in sorted(polinomio.items()))
        for polinomio in residuos
    )
