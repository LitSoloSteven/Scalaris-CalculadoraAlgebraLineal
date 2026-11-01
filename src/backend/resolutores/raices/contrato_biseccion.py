"""Contrato de entrada y salida del motor de bisección con precisión entera."""
import math
from dataclasses import dataclass, field
from fractions import Fraction

D_MAXIMO = 15
LIMITE_ITERACIONES_DEFECTO = 100
LONGITUD_MAXIMA_EXPRESION = 512


@dataclass(frozen=True)
class EntradaBiseccion:
    """Expresión, intervalo, precisión decimal y límite de iteraciones validados."""

    expresion: str
    a: float
    b: float
    d: int
    limite_iteraciones: int = LIMITE_ITERACIONES_DEFECTO

    @property
    def error_absoluto(self) -> Fraction:
        """Umbral E = 10^(-d) en fracción exacta."""
        return Fraction(1, 10 ** self.d)


@dataclass(frozen=True)
class IteracionBiseccion:
    """Registro inmutable de una iteración del método."""

    i: int
    a: float
    b: float
    c: float
    f_a: float
    f_b: float
    f_c: float
    ancho: float
    cota: float
    residuo: float
    error_relativo: str
    explicacion: str


@dataclass(frozen=True)
class ResultadoBiseccion:
    """Resultado completo del método con estado, intervalo final y métricas."""

    estado: str
    mensaje: str
    aproximacion: float | None = None
    intervalo_final: tuple[float, float] | None = None
    E: Fraction | None = None
    cota: float | None = None
    iteraciones: tuple[IteracionBiseccion, ...] = ()
    motivo_parada: str = ""
    metricas: dict = field(default_factory=dict)


def validar_precision(valor) -> int:
    """Rechaza d no entero, booleano o fuera de rango; devuelve el entero validado."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(
            f"La precisión d debe ser un entero (recibido {type(valor).__name__}: {valor!r})."
        )
    if valor < 0 or valor > D_MAXIMO:
        raise ValueError(f"La precisión d debe estar entre 0 y {D_MAXIMO} (recibido {valor}).")
    return valor


def derivar_E(d: int) -> Fraction:
    """Devuelve 10^(-d) como fracción exacta; lanza ValueError si d es inválido."""
    precision = validar_precision(d)
    return Fraction(1, 10 ** precision)


def validar_entrada(datos: dict) -> EntradaBiseccion:
    """Valida una carga cruda y devuelve la entrada canónica; lanza ValueError granular."""
    if not isinstance(datos, dict):
        raise ValueError("La entrada debe ser un diccionario con la expresion y el intervalo.")
    expresion = _validar_expresion(datos.get("expresion"))
    a = _validar_extremo(datos.get("a"), "a")
    b = _validar_extremo(datos.get("b"), "b")
    if a >= b:
        raise ValueError(f"El intervalo es inválido: a ({a}) debe ser menor que b ({b}).")
    d = validar_precision(datos.get("d"))
    limite = _validar_limite(datos.get("limite_iteraciones"))
    return EntradaBiseccion(expresion=expresion, a=a, b=b, d=d, limite_iteraciones=limite)


def _validar_expresion(valor) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("La expresión f(x) es obligatoria y no puede estar vacía.")
    if len(valor) > LONGITUD_MAXIMA_EXPRESION:
        raise ValueError(f"La expresión excede {LONGITUD_MAXIMA_EXPRESION} caracteres.")
    return valor.strip()


def _validar_extremo(valor, nombre: str) -> float:
    if isinstance(valor, bool):
        raise ValueError(f"El extremo {nombre} no puede ser booleano.")
    if not isinstance(valor, (int, float)):
        raise ValueError(f"El extremo {nombre} debe ser numérico (recibido {valor!r}).")
    numero = float(valor)
    if not math.isfinite(numero):
        raise ValueError(f"El extremo {nombre} debe ser finito (recibido {valor!r}).")
    return numero


def _validar_limite(valor) -> int:
    if valor is None:
        return LIMITE_ITERACIONES_DEFECTO
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(
            f"El límite de iteraciones debe ser un entero positivo (recibido {valor!r})."
        )
    return valor