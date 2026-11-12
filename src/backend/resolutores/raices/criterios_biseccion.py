"""Configuración y validación de criterios independientes de bisección."""
from dataclasses import dataclass
from fractions import Fraction

from .limites_biseccion import D_MAXIMO
from .validacion_raices import validar_tolerancia_positiva

_UNIDADES = {"relativo": "%", "ancho": "unidades de x", "decimales": "unidades de x",
             "residuo": "unidades de f(x)", "iteraciones": "iteraciones"}


@dataclass(frozen=True)
class CriterioParada:
    """Tipo de condición y parámetro solicitado, independientes del formato visual."""

    tipo: str
    parametro: int | float

    @property
    def unidad(self) -> str:
        """Devuelve la unidad de la métrica comparada con el umbral."""
        return _UNIDADES[self.tipo]

    @property
    def umbral(self) -> Fraction | float | int:
        """Devuelve el umbral sin redondear; los decimales usan una fracción exacta."""
        return tolerancia_decimal(self.parametro) if self.tipo == "decimales" else self.parametro


def tolerancia_decimal(decimales: int) -> Fraction:
    """Devuelve el umbral decimal exacto; lanza ValueError antes de operar con una precisión inválida."""
    precision = validar_entero_criterio(decimales, "La precisión decimales", D_MAXIMO)
    return Fraction(1, 10 ** precision)


def validar_entero_criterio(valor: object, etiqueta: str, maximo: int, minimo: int = 0) -> int:
    """Devuelve un entero dentro de sus límites; lanza ValueError sin truncar ni aceptar booleanos."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{etiqueta} debe ser un entero.")
    if not minimo <= valor <= maximo:
        raise ValueError(f"{etiqueta} debe estar entre {minimo} y {maximo}.")
    return valor


def validar_criterio(valor: object, decimales: int, limite: int) -> CriterioParada:
    """Normaliza criterio o carga antigua; lanza ValueError ante tipos, umbrales o conteos inválidos."""
    if valor is None:
        valor = CriterioParada("decimales", decimales)
    if isinstance(valor, dict):
        if set(valor) != {"tipo", "parametro"}:
            raise ValueError("El criterio requiere solamente tipo y parametro.")
        valor = CriterioParada(valor["tipo"], valor["parametro"])
    if not isinstance(valor, CriterioParada):
        raise ValueError("El criterio de parada es inválido.")
    if not isinstance(valor.tipo, str) or valor.tipo not in _UNIDADES:
        raise ValueError("El tipo de criterio no está permitido.")
    parametro = _validar_parametro(valor, limite)
    return CriterioParada(valor.tipo, parametro)


def _validar_parametro(criterio: CriterioParada, limite: int) -> int | float:
    if criterio.tipo == "decimales":
        return validar_entero_criterio(criterio.parametro, "La precisión decimales", D_MAXIMO)
    if criterio.tipo == "iteraciones":
        return validar_entero_criterio(criterio.parametro, "El número fijo de iteraciones", limite, 1)
    return validar_tolerancia_positiva(criterio.parametro)
