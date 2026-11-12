"""Motor de Newton-Raphson para resolver ecuaciones no lineales."""
from dataclasses import dataclass, field
import math

from .evaluador_funcion import compilar, evaluar
from .limites_raices import LIMITE_ITERACIONES_DEFECTO
from .validacion_raices import validar_expresion, validar_extremo, validar_limite_iteraciones


@dataclass(frozen=True, kw_only=True)
class EntradaNewtonRaphson:
    """Datos de entrada: función, derivada, aproximación y criterios de parada."""
    expresion: str
    derivada: str
    aproximacion_inicial: float
    tolerancia: float = 1e-6
    limite_iteraciones: int = LIMITE_ITERACIONES_DEFECTO


@dataclass(frozen=True)
class IteracionNewtonRaphson:
    """Registro inmutable de una aproximación de Newton y sus métricas."""
    i: int
    x_actual: float
    valor_funcion: float
    valor_derivada: float
    x_siguiente: float
    valor_siguiente: float
    error_absoluto: float
    error_relativo_porcentual: float | None


@dataclass(frozen=True)
class ResultadoNewtonRaphson:
    """Estado, raíz aproximada y procedimiento iterativo del método."""
    metodo: str = field(default="newton_raphson", init=False)
    entrada: EntradaNewtonRaphson | None = None
    estado: str = "ERROR"
    mensaje: str = ""
    codigo_diagnostico: str = ""
    motivo_parada: str = ""
    aproximacion: float | None = None
    residuo: float | None = None
    iteraciones: tuple[IteracionNewtonRaphson, ...] = ()
    iteraciones_totales: int = 0


def newton_raphson(entrada: EntradaNewtonRaphson) -> ResultadoNewtonRaphson:
    """Calcula una raíz con x(n+1) = x(n) - f(x(n))/f'(x(n))."""
    try:
        entrada = _validar_entrada(entrada)
    except (TypeError, ValueError, OverflowError) as error:
        return _error(None, error, "ENTRADA_INVALIDA", "entrada_invalida")

    try:
        funcion = compilar(entrada.expresion)
        derivada = compilar(entrada.derivada)
    except (TypeError, ValueError) as error:
        return _error(entrada, error, "EXPRESION_INVALIDA", "expresion_invalida")

    x_actual = entrada.aproximacion_inicial
    try:
        f_actual = evaluar(funcion, x_actual)
    except ValueError as error:
        return _error(entrada, error, _codigo_evaluacion(error), "evaluacion_inicial")

    if f_actual == 0:
        return _resultado(
            entrada, "EXITO", "La aproximación inicial ya es una raíz.",
            "RAIZ_INICIAL", "raiz_inicial", x_actual, 0.0, [],
        )

    filas: list[IteracionNewtonRaphson] = []
    for indice in range(1, entrada.limite_iteraciones + 1):
        try:
            df_actual = evaluar(derivada, x_actual)
        except ValueError as error:
            return _error(
                entrada, error, _codigo_evaluacion(error), "evaluacion_derivada",
                filas, aproximacion=x_actual, residuo=abs(f_actual),
            )

        if df_actual == 0:
            return _error(
                entrada,
                ValueError("La derivada vale cero en la aproximación actual; no se puede dividir entre ella."),
                "DERIVADA_CERO",
                "derivada_cero",
                filas,
                aproximacion=x_actual,
                residuo=abs(f_actual),
            )

        try:
            siguiente = x_actual - f_actual / df_actual
            if not math.isfinite(siguiente):
                raise ValueError("La nueva aproximación excede la capacidad numérica.")
            f_siguiente = evaluar(funcion, siguiente)
            error_absoluto = abs(siguiente - x_actual)
            if not math.isfinite(error_absoluto):
                raise ValueError("El error entre aproximaciones no es representable.")
        except (ArithmeticError, ValueError) as error:
            return _error(
                entrada, error, _codigo_evaluacion(error), "evaluacion_iteracion",
                filas, aproximacion=x_actual, residuo=abs(f_actual),
            )

        error_relativo = None
        if siguiente != 0:
            relativo = abs((siguiente - x_actual) / siguiente) * 100
            if math.isfinite(relativo):
                error_relativo = relativo

        filas.append(IteracionNewtonRaphson(
            i=indice,
            x_actual=x_actual,
            valor_funcion=f_actual,
            valor_derivada=df_actual,
            x_siguiente=siguiente,
            valor_siguiente=f_siguiente,
            error_absoluto=error_absoluto,
            error_relativo_porcentual=error_relativo,
        ))

        if abs(f_siguiente) <= entrada.tolerancia:
            return _resultado(
                entrada, "EXITO", "La aproximación cumple la tolerancia del residuo.",
                "CONVERGENCIA_RESIDUO", "tolerancia_residuo",
                siguiente, abs(f_siguiente), filas,
            )

        if siguiente == x_actual:
            return _resultado(
                entrada, "ESTANCAMIENTO",
                "La aproximación dejó de cambiar por la precisión numérica, pero el residuo aún supera la tolerancia.",
                "ESTANCAMIENTO", "estancamiento_numerico",
                siguiente, abs(f_siguiente), filas,
            )

        if error_absoluto <= entrada.tolerancia:
            return _resultado(
                entrada, "EXITO",
                "La diferencia entre aproximaciones consecutivas cumple la tolerancia.",
                "CONVERGENCIA_POR_ERROR", "error_absoluto",
                siguiente, abs(f_siguiente), filas,
            )

        x_actual, f_actual = siguiente, f_siguiente

    ultima = filas[-1]
    return _resultado(
        entrada, "LIMITE_ITERACIONES",
        f"Se alcanzó el límite de {entrada.limite_iteraciones} iteraciones sin cumplir la tolerancia.",
        "LIMITE_ITERACIONES", "limite_iteraciones",
        ultima.x_siguiente, abs(ultima.valor_siguiente), filas,
    )


def _validar_entrada(entrada: EntradaNewtonRaphson) -> EntradaNewtonRaphson:
    """Normaliza expresiones y comprueba los datos escalares del método."""
    if not isinstance(entrada, EntradaNewtonRaphson):
        raise ValueError("La entrada debe cumplir el contrato de Newton-Raphson.")

    expresion = validar_expresion(entrada.expresion)
    derivada = validar_expresion(entrada.derivada)
    inicial = validar_extremo(entrada.aproximacion_inicial, "x₀")
    tolerancia = validar_extremo(entrada.tolerancia, "La tolerancia")
    if tolerancia <= 0:
        raise ValueError("La tolerancia debe ser un número real positivo.")

    limite = validar_limite_iteraciones(entrada.limite_iteraciones)
    return EntradaNewtonRaphson(
        expresion=expresion,
        derivada=derivada,
        aproximacion_inicial=inicial,
        tolerancia=tolerancia,
        limite_iteraciones=limite,
    )


def _codigo_evaluacion(error: ValueError) -> str:
    """Conserva el diagnóstico numérico que aporta el evaluador compartido."""
    return getattr(error, "codigo", "DOMINIO_INVALIDO")


def _error(
    entrada: EntradaNewtonRaphson | None,
    error: Exception,
    codigo: str,
    motivo: str,
    filas: list[IteracionNewtonRaphson] | None = None,
    *,
    aproximacion: float | None = None,
    residuo: float | None = None,
) -> ResultadoNewtonRaphson:
    """Construye un resultado de error y conserva el procedimiento válido."""
    return _resultado(
        entrada, "ERROR", str(error), codigo, motivo,
        aproximacion, residuo, filas or [],
    )


def _resultado(
    entrada: EntradaNewtonRaphson | None,
    estado: str,
    mensaje: str,
    codigo: str,
    motivo: str,
    aproximacion: float | None,
    residuo: float | None,
    filas: list[IteracionNewtonRaphson],
) -> ResultadoNewtonRaphson:
    """Centraliza la salida para mantener coherentes el estado y la traza."""
    return ResultadoNewtonRaphson(
        entrada=entrada,
        estado=estado,
        mensaje=mensaje,
        codigo_diagnostico=codigo,
        motivo_parada=motivo,
        aproximacion=aproximacion,
        residuo=residuo,
        iteraciones=tuple(filas),
        iteraciones_totales=len(filas),
    )
