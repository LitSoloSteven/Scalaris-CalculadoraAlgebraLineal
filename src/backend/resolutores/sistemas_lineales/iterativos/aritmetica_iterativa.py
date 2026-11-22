"""Aritmética exacta y presupuesto de crecimiento para métodos iterativos."""
from dataclasses import dataclass
from fractions import Fraction

from .limites_iterativos import fraccion_admitida


class LimiteAritmeticoIterativo(ArithmeticError):
    """Señala que el cálculo exacto superó el presupuesto configurado."""


class LimiteTamanoIterativo(LimiteAritmeticoIterativo):
    """Señala que una fracción excede su cota de bits, sin reiniciar el presupuesto."""


class LimiteResiduoIterativo(LimiteTamanoIterativo):
    """Señala que una componente final del residuo excede su cota de bits."""


@dataclass(frozen=True, kw_only=True)
class ConfiguracionAritmetica:
    """Agrupa los topes que usan el presupuesto, la validación y la traza."""

    maximo_operaciones: int
    maximo_bits_entrada: int
    maximo_bits_calculo: int
    maximo_bits_cambio: int
    maximo_bits_acumulacion: int

    @property
    def maximo_bits_residuo(self) -> int:
        """Acota b - A·x con los bits de la acumulación, los de b y un acarreo."""
        return self.maximo_bits_acumulacion + self.maximo_bits_entrada + 1


class PresupuestoAritmetico:
    """Cuenta operaciones exactas y rechaza fracciones fuera del tamaño admitido."""

    def __init__(
        self, configuracion: ConfiguracionAritmetica, operaciones: int | None = None,
    ) -> None:
        """Inicia el contador con el tope recibido o el límite de la configuración."""
        self.configuracion = configuracion
        self.restantes = (
            configuracion.maximo_operaciones if operaciones is None else operaciones
        )

    def consumir(self, cantidad: int = 1) -> None:
        """Descuenta operaciones y lanza el límite cuando ya no quedan disponibles."""
        self.restantes -= cantidad
        if self.restantes < 0:
            raise LimiteAritmeticoIterativo(
                "El cálculo exacto superó el presupuesto de operaciones."
            )

    def registrar(
        self, valor: Fraction, maximo_bits: int | None = None,
    ) -> Fraction:
        """Comprueba el tamaño de la fracción y la devuelve sin modificarla."""
        limite = self.configuracion.maximo_bits_calculo if maximo_bits is None else maximo_bits
        if not fraccion_admitida(valor, limite):
            raise LimiteTamanoIterativo(
                "El cálculo exacto superó el tamaño máximo de una fracción."
            )
        return valor


def _sumar_producto(
    total: Fraction,
    coeficiente: Fraction,
    componente: Fraction,
    presupuesto: PresupuestoAritmetico,
) -> Fraction:
    """Suma un producto exacto y contabiliza la multiplicación y la suma."""
    presupuesto.consumir(2)
    return presupuesto.registrar(
        total + coeficiente * componente,
        presupuesto.configuracion.maximo_bits_acumulacion,
    )


def producto_fila(
    fila: tuple[Fraction, ...],
    vector: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> Fraction:
    """Devuelve el producto escalar exacto de una fila y un vector de igual dimensión."""
    if len(fila) != len(vector):
        raise ValueError("La fila y el vector deben tener la misma dimensión.")
    total = Fraction(0)
    for coeficiente, componente in zip(fila, vector):
        total = _sumar_producto(total, coeficiente, componente, presupuesto)
    return total


def producto_fila_sin_diagonal(
    fila: tuple[Fraction, ...],
    indice: int,
    vector: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> Fraction:
    """Suma los productos de una fila omitiendo el coeficiente diagonal."""
    if len(fila) != len(vector):
        raise ValueError("La fila y el vector deben tener la misma dimensión.")
    total = Fraction(0)
    for posicion, coeficiente in enumerate(fila):
        if posicion != indice:
            total = _sumar_producto(total, coeficiente, vector[posicion], presupuesto)
    return total


def producto_fila_mixto(
    fila: tuple[Fraction, ...],
    indice: int,
    vector_anterior: tuple[Fraction, ...],
    vector_trabajo: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> Fraction:
    """Suma la fila con valores nuevos antes de la diagonal y anteriores después.
    Exige que ambos vectores tengan la dimensión de la fila."""
    if len(fila) != len(vector_anterior) or len(fila) != len(vector_trabajo):
        raise ValueError("La fila y los vectores deben tener la misma dimensión.")
    total = Fraction(0)
    for posicion, coeficiente in enumerate(fila):
        if posicion != indice:
            vector = vector_trabajo if posicion < indice else vector_anterior
            total = _sumar_producto(total, coeficiente, vector[posicion], presupuesto)
    return total


def residuo_sistema(
    matriz: tuple[tuple[Fraction, ...], ...],
    vector_b: tuple[Fraction, ...],
    vector: tuple[Fraction, ...],
    presupuesto: PresupuestoAritmetico,
) -> tuple[Fraction, ...]:
    """Devuelve b - A·x componente a componente; exige dimensiones coincidentes."""
    if len(matriz) != len(vector_b) or any(len(fila) != len(vector) for fila in matriz):
        raise ValueError("La matriz, b y la aproximación deben coincidir en dimensión.")
    residuo = []
    for termino, fila in zip(vector_b, matriz):
        producto = producto_fila(fila, vector, presupuesto)
        presupuesto.consumir()
        try:
            residuo.append(presupuesto.registrar(
                termino - producto, presupuesto.configuracion.maximo_bits_residuo,
            ))
        except LimiteTamanoIterativo as error:
            raise LimiteResiduoIterativo(str(error)) from error
    return tuple(residuo)


def norma_infinito(vector: tuple[Fraction, ...]) -> Fraction:
    """Devuelve el máximo de los valores absolutos de un vector no vacío."""
    return max(abs(componente) for componente in vector)
