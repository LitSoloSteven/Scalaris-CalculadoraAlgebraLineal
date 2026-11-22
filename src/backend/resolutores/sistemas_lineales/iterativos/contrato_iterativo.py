"""Datos comunes de entrada y salida de los métodos iterativos."""
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Literal

EscalarIterativo = Fraction | int | str
FilaCapturaIterativa = list[EscalarIterativo] | tuple[EscalarIterativo, ...]
MatrizCrudaIterativa = list[FilaCapturaIterativa] | tuple[FilaCapturaIterativa, ...]
VectorIterativo = tuple[Fraction, ...]
CodigoIterativo = Literal[
    "SOLUCION_EXACTA",
    "TOLERANCIA_ALCANZADA",
    "MAXIMO_ITERACIONES",
    "LIMITE_ARITMETICO",
    "DIAGONAL_NULA",
    "ENTRADA_INVALIDA",
]
CampoIterativo = Literal[
    "entrada", "matriz_a", "vector_b", "vector_inicial", "tolerancia", "maximo_iteraciones",
]


@dataclass(frozen=True, kw_only=True)
class EntradaIterativa:
    """Recibe la cuadrícula original de coeficientes y admite texto racional en todos los escalares.
    La tolerancia positiva acota la norma infinito de b - A·x. El máximo cuenta barridos completos."""

    matriz_a: MatrizCrudaIterativa
    vector_b: tuple[EscalarIterativo, ...]
    vector_inicial: tuple[EscalarIterativo, ...]
    tolerancia: EscalarIterativo
    maximo_iteraciones: int


@dataclass(frozen=True, kw_only=True)
class EntradaCanonicaIterativa:
    """Conserva A, b, el inicio y los parámetros validados como racionales inmutables.
    Las filas mantienen el orden original para reconstruir cada sustitución de la traza."""

    matriz: tuple[VectorIterativo, ...]
    vector_b: VectorIterativo
    vector_inicial: VectorIterativo
    tolerancia: Fraction
    maximo_iteraciones: int
    dominancia_estricta: bool


@dataclass(frozen=True, kw_only=True)
class DiagnosticoIterativo:
    """Mensaje en español con campo y coordenadas desde 1 cuando se conocen.
    En un vector, la fila identifica la componente. La columna se usa en la matriz."""

    mensaje: str
    campo: CampoIterativo | None = None
    fila: int | None = None
    columna: int | None = None


@dataclass(frozen=True, kw_only=True)
class PasoIterativo:
    """Barrido completo con índice desde 1, vectores y normas infinito exactas.
    La traza conserva el vector previo y el actualizado para reproducir cada sustitución."""

    indice: int
    vector_anterior: VectorIterativo
    vector_nuevo: VectorIterativo
    norma_cambio: Fraction
    norma_residuo: Fraction


@dataclass(frozen=True, kw_only=True)
class ResultadoIterativo:
    """Causa de parada y traza inmutable; aproximación y residuo son None hasta verificar un vector.
    La entrada canónica se serializa como metadato, sin intervenir en la igualdad ni el hash."""

    codigo: CodigoIterativo
    aproximacion: VectorIterativo | None = None
    residuo: VectorIterativo | None = None
    norma_residuo: Fraction | None = None
    dominancia_estricta: bool | None = None
    pasos: tuple[PasoIterativo, ...] = ()
    diagnostico: DiagnosticoIterativo | None = None
    entrada_canonica: EntradaCanonicaIterativa | None = field(default=None, compare=False)

    @property
    def iteraciones_realizadas(self) -> int:
        """Devuelve el número de barridos completos en la traza."""
        return len(self.pasos)

    @property
    def explicacion(self) -> str:
        """Describe en español la causa de parada y el vector verificado.
        Con vector completo resume el cierre; sin vector devuelve el diagnóstico."""
        if self.aproximacion is None or self.norma_residuo is None:
            return _explicar_sin_vector(self.diagnostico)
        if self.codigo == "SOLUCION_EXACTA":
            return _explicar_exacta(self.aproximacion, self.iteraciones_realizadas)
        if self.codigo == "TOLERANCIA_ALCANZADA":
            return _explicar_tolerancia(
                self.aproximacion, self.iteraciones_realizadas, self.norma_residuo,
            )
        if self.codigo == "MAXIMO_ITERACIONES":
            return _explicar_maximo(
                self.aproximacion, self.iteraciones_realizadas, self.norma_residuo,
            )
        return _explicar_limite(
            self.aproximacion, self.iteraciones_realizadas, self.norma_residuo,
        )


def _explicar_sin_vector(diagnostico: DiagnosticoIterativo | None) -> str:
    """Devuelve el diagnóstico disponible o un aviso cuando no se verificó un vector."""
    if diagnostico is not None:
        return diagnostico.mensaje
    return "No se pudo verificar una aproximación del sistema."


def _formatear_vector(vector: VectorIterativo) -> str:
    """Presenta un vector entre paréntesis con sus componentes separadas por comas."""
    return "(" + ", ".join(str(componente) for componente in vector) + ")"


def _describir_barridos(iteraciones: int) -> str:
    """Devuelve el conteo de barridos con singular o plural."""
    unidad = "barrido" if iteraciones == 1 else "barridos"
    return f"{iteraciones} {unidad}"


def _explicar_exacta(vector: VectorIterativo, iteraciones: int) -> str:
    """Describe una solución exacta y si el vector inicial ya la satisfacía."""
    texto = _formatear_vector(vector)
    if iteraciones == 0:
        return f"El vector inicial ya era una solución exacta {texto}."
    return f"El método encontró una solución exacta {texto} tras {_describir_barridos(iteraciones)}."


def _explicar_tolerancia(
    vector: VectorIterativo, iteraciones: int, norma: Fraction,
) -> str:
    """Describe la aproximación que cumple la tolerancia solicitada."""
    return (
        f"La aproximación {_formatear_vector(vector)} cumple la tolerancia con una "
        f"norma del residuo de {norma} tras {_describir_barridos(iteraciones)}."
    )


def _explicar_maximo(
    vector: VectorIterativo, iteraciones: int, norma: Fraction,
) -> str:
    """Describe el cierre por máximo sin ocultar el último residuo."""
    return (
        f"Se alcanzó el máximo de {_describir_barridos(iteraciones)} con la "
        f"aproximación {_formatear_vector(vector)} y una norma del residuo de {norma}."
    )


def _explicar_limite(
    vector: VectorIterativo, iteraciones: int, norma: Fraction,
) -> str:
    """Describe el límite aritmético que conserva la última aproximación completa."""
    return (
        f"El cálculo se interrumpió por el límite aritmético tras "
        f"{_describir_barridos(iteraciones)}; se conserva la aproximación "
        f"{_formatear_vector(vector)} con una norma del residuo de {norma}."
    )
