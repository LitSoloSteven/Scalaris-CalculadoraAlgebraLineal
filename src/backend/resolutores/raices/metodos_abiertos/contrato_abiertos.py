"""Contrato de entrada y salida de los métodos abiertos de resolución de raíces."""
from dataclasses import dataclass
from typing import Literal

MetodoAbierto = Literal["newton", "secante"]
EstadoAbierto = Literal[
    "EXITO",
    "LIMITE_ITERACIONES",
    "DERIVADA_NULA",
    "DENOMINADOR_NULO",
    "DIVERGENCIA",
    "ERROR",
]
CriterioParada = Literal["", "residuo", "cambio"]
AVISO_CAMBIO_SIN_RESIDUO = (
    "La aproximación se estabilizó, pero el residuo todavía supera la tolerancia. "
    "Revisa el resultado."
)


@dataclass(frozen=True, kw_only=True)
class EntradaMetodoAbierto:
    """Expresión, puntos iniciales y límites validados para un método abierto."""

    metodo: MetodoAbierto
    expresion: str
    x0: float
    x1: float | None = None
    tolerancia: float = 1e-6
    limite_iteraciones: int = 100


@dataclass(frozen=True)
class IteracionMetodoAbierto:
    """Registro inmutable de una iteración con la aproximación siguiente ya evaluada."""

    i: int
    x_anterior: float | None
    f_x_anterior: float | None
    x_n: float
    f_x_n: float
    derivada: float | None
    x_siguiente: float | None
    f_x_siguiente: float | None
    residuo: float | None
    error_absoluto: float | None
    error_relativo_porcentual: float | None
    criterio: CriterioParada = ""


@dataclass(frozen=True)
class ResultadoMetodoAbierto:
    """Resultado completo del método con estado, raíz aproximada y trazabilidad."""

    metodo: MetodoAbierto
    entrada: EntradaMetodoAbierto | None = None
    estado: EstadoAbierto = "ERROR"
    mensaje: str = ""
    codigo_diagnostico: str = ""
    raiz: float | None = None
    residuo: float | None = None
    iteraciones: tuple[IteracionMetodoAbierto, ...] = ()
    iteraciones_totales: int = 0
    derivada_expresion: str | None = None
    advertencias: tuple[str, ...] = ()
    contexto_fallo: dict | None = None


def resultado_metodo(
    metodo: MetodoAbierto,
    iteraciones: tuple[IteracionMetodoAbierto, ...] = (),
    **datos: object,
) -> ResultadoMetodoAbierto:
    """Construye el resultado y calcula su total de iteraciones.

    Args:
        metodo: Método que produjo el resultado.
        iteraciones: Traza que se conservará en el resultado.
        **datos: Campos adicionales del contrato de salida.

    Returns:
        Resultado con total de iteraciones igual a la longitud de la traza.
    """
    return ResultadoMetodoAbierto(
        metodo=metodo,
        iteraciones=iteraciones,
        iteraciones_totales=len(iteraciones),
        **datos,
    )


def resultado_error(
    metodo: MetodoAbierto, codigo: str, mensaje: str, **datos: object
) -> ResultadoMetodoAbierto:
    """Construye un resultado de error general.

    Args:
        metodo: Método que produjo el error.
        codigo: Código estable del diagnóstico.
        mensaje: Explicación legible del error.
        **datos: Campos adicionales del contrato de salida.

    Returns:
        Resultado en estado ERROR.
    """
    return resultado_fallo(metodo, "ERROR", codigo, mensaje, **datos)


def resultado_fallo(
    metodo: MetodoAbierto, estado: EstadoAbierto, codigo: str, mensaje: str, **datos: object
) -> ResultadoMetodoAbierto:
    """Construye un resultado fallido con el estado específico del motor.

    Args:
        metodo: Método que produjo el fallo.
        estado: Estado terminal del método.
        codigo: Código estable del diagnóstico.
        mensaje: Explicación legible del fallo.
        **datos: Campos adicionales del contrato de salida.

    Returns:
        Resultado con el estado y el diagnóstico indicados.
    """
    return resultado_metodo(
        metodo,
        estado=estado,
        codigo_diagnostico=codigo,
        mensaje=mensaje,
        **datos,
    )


def resultado_evaluacion(
    metodo: MetodoAbierto, abscisa: float, detalle: str, **datos: object
) -> ResultadoMetodoAbierto:
    """Construye un error de evaluación asociado a una abscisa.

    Args:
        metodo: Método que encontró el error.
        abscisa: Punto donde falló la evaluación.
        detalle: Motivo informado por el evaluador.
        **datos: Campos adicionales del contrato de salida.

    Returns:
        Resultado ERROR con el punto y el detalle en el contexto de fallo.
    """
    return resultado_error(
        metodo,
        "EVALUACION",
        f"No se pudo evaluar la función en x = {abscisa:g}: {detalle}",
        contexto_fallo={"x": abscisa, "detalle": detalle},
        **datos,
    )


def resultado_inicial(
    metodo: MetodoAbierto,
    entrada: EntradaMetodoAbierto,
    abscisa: float,
    f_x: float,
    **datos: object,
) -> ResultadoMetodoAbierto:
    """Construye el éxito inmediato de un punto inicial que cumple tolerancia.

    Args:
        metodo: Método que evaluó el punto.
        entrada: Entrada validada usada por el método.
        abscisa: Punto inicial evaluado.
        f_x: Valor de la función en el punto.
        **datos: Campos adicionales del contrato de salida.

    Returns:
        Resultado EXITO con diagnóstico de raíz exacta o tolerancia cumplida.
    """
    codigo = "PUNTO_INICIAL_RAIZ" if f_x == 0 else "PUNTO_INICIAL_TOLERANCIA"
    mensaje = (
        "El punto inicial ya es una raíz exacta."
        if f_x == 0
        else "El punto inicial ya cumple la tolerancia de residuo."
    )
    return resultado_metodo(
        metodo,
        entrada=entrada,
        estado="EXITO",
        codigo_diagnostico=codigo,
        mensaje=mensaje,
        raiz=abscisa,
        residuo=abs(f_x),
        **datos,
    )


def resultado_convergencia(
    metodo: MetodoAbierto,
    entrada: EntradaMetodoAbierto,
    iteraciones: tuple[IteracionMetodoAbierto, ...],
    criterio: Literal["residuo", "cambio"],
    **datos: object,
) -> ResultadoMetodoAbierto:
    """Construye el éxito por residuo o por cambio de aproximación.

    Args:
        metodo: Método que convergió.
        entrada: Entrada validada usada por el método.
        iteraciones: Traza hasta la aproximación aceptada.
        criterio: Criterio de parada que se cumplió.
        **datos: Campos adicionales del contrato de salida.

    Returns:
        Resultado EXITO con código correspondiente al criterio de parada.
    """
    codigo = "TOLERANCIA_RESIDUO" if criterio == "residuo" else "TOLERANCIA_CAMBIO"
    mensaje = (
        "Convergió por tolerancia de residuo."
        if criterio == "residuo"
        else "Convergió por cambio de aproximación."
    )
    return resultado_metodo(
        metodo,
        iteraciones,
        entrada=entrada,
        estado="EXITO",
        codigo_diagnostico=codigo,
        mensaje=mensaje,
        **datos,
    )


def resultado_limite(
    metodo: MetodoAbierto,
    entrada: EntradaMetodoAbierto,
    iteraciones: tuple[IteracionMetodoAbierto, ...],
    **datos: object,
) -> ResultadoMetodoAbierto:
    """Construye el resultado de límite sin tolerancia alcanzada.

    Args:
        metodo: Método que alcanzó el máximo.
        entrada: Entrada validada usada por el método.
        iteraciones: Traza calculada antes de alcanzar el máximo.
        **datos: Campos adicionales del contrato de salida.

    Returns:
        Resultado LIMITE_ITERACIONES con su traza.
    """
    return resultado_metodo(
        metodo,
        iteraciones,
        entrada=entrada,
        estado="LIMITE_ITERACIONES",
        codigo_diagnostico="LIMITE_ITERACIONES",
        mensaje="No se alcanzó la tolerancia en el máximo de iteraciones.",
        **datos,
    )
