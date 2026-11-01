"""Motor de resolución de raíces por el método de bisección."""
import math
from src.backend.resolutores.raices.contrato_biseccion import (
    EntradaBiseccion, IteracionBiseccion, ResultadoBiseccion
)
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar
from src.backend.excepciones import ErrorDominio, ErrorNoFinito


def biseccion(entrada: EntradaBiseccion) -> ResultadoBiseccion:
    """Ejecuta el método de bisección sobre la entrada validada."""
    try:
        f = compilar(entrada.expresion)
        fa = evaluar(f, entrada.a)
        fb = evaluar(f, entrada.b)
    except (ValueError, ErrorDominio, ErrorNoFinito) as error:
        return ResultadoBiseccion(estado="ERROR", mensaje=str(error))

    inicial = _validar_extremos(entrada, fa, fb)
    if inicial is not None:
        return inicial

    E = entrada.error_absoluto
    a, b = entrada.a, entrada.b
    iteraciones, c_previo, motivo = [], None, ""

    for i in range(1, entrada.limite_iteraciones + 1):
        c = (a + b) / 2.0
        try:
            fc = evaluar(f, c)
        except (ErrorDominio, ErrorNoFinito) as error:
            return ResultadoBiseccion(estado="ERROR", mensaje=f"Error en iteración {i}: {error}", iteraciones=tuple(iteraciones))

        iteraciones.append(_crear_iteracion(i, c, fc, (a, b, fa, fb), c_previo))
        if fc == 0.0:
            motivo = "raiz_exacta"
            break
        if (b - a) < E:
            motivo = "ancho_menor_que_E"
            break
        (a, fa), (b, fb) = _actualizar_intervalo((a, fa), (b, fb), (c, fc))
        c_previo = c
    else:
        motivo = "limite_iteraciones"

    return _construir_resultado((a, b), entrada, motivo, iteraciones, f)


def _validar_extremos(entrada: EntradaBiseccion, fa: float, fb: float) -> ResultadoBiseccion | None:
    """Detecta raíces exactas en los extremos o la ausencia de cambio de signo."""
    if fa == 0.0 or fb == 0.0:
        es_extremo_a = fa == 0.0
        return ResultadoBiseccion(
            estado="EXITO",
            mensaje=f"La raíz está exactamente en el extremo {'a' if es_extremo_a else 'b'}.",
            aproximacion=entrada.a if es_extremo_a else entrada.b,
            intervalo_final=(entrada.a, entrada.b),
            E=entrada.error_absoluto,
            cota=(entrada.b - entrada.a) / 2.0,
            iteraciones=(),
            motivo_parada="raiz_exacta",
            metricas={"iteraciones_totales": 0, "residuo_final": 0.0}
        )
    if math.copysign(1.0, fa) == math.copysign(1.0, fb):
        return ResultadoBiseccion(
            estado="SIN_CAMBIO_DE_SIGNO",
            mensaje=f"f(a)={fa} y f(b)={fb} tienen el mismo signo."
        )
    return None


def _crear_iteracion(i: int, c: float, fc: float, estado: tuple[float, float, float, float], c_previo: float | None) -> IteracionBiseccion:
    """Construye el registro inmutable de una iteración."""
    a, b, fa, fb = estado
    return IteracionBiseccion(
        i=i, a=a, b=b, c=c, f_a=fa, f_b=fb, f_c=fc,
        ancho=b - a, cota=(b - a) / 2.0, residuo=abs(fc),
        error_relativo=_calcular_error_relativo(c, c_previo),
        explicacion=_explicar_intervalo(a, b, c, fa, fc)
    )


def _calcular_error_relativo(c: float, c_previo: float | None) -> str:
    if c_previo is None or c == 0:
        return "No aplica"
    return f"{abs((c - c_previo) / c) * 100:.2f}%"


def _explicar_intervalo(a: float, b: float, c: float, fa: float, fc: float) -> str:
    if math.copysign(1.0, fa) != math.copysign(1.0, fc):
        return f"Se conserva [{a}, {c}] porque f(a) y f(c) tienen signos opuestos."
    return f"Se conserva [{c}, {b}] porque f(c) y f(b) tienen signos opuestos."


def _actualizar_intervalo(inferior: tuple[float, float], superior: tuple[float, float], medio: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    """Conserva el subintervalo que encierra la raíz y devuelve los extremos y sus valores."""
    a, fa = inferior
    b, fb = superior
    c, fc = medio
    if math.copysign(1.0, fa) != math.copysign(1.0, fc):
        return (a, fa), (c, fc)
    return (c, fc), (b, fb)


def _construir_resultado(intervalo: tuple[float, float], entrada: EntradaBiseccion, motivo: str, iteraciones: list, f) -> ResultadoBiseccion:
    a, b = intervalo
    aprox = (a + b) / 2.0
    cota_final = (b - a) / 2.0
    estado = "EXITO" if motivo != "limite_iteraciones" else "PRECISION_NO_ALCANZADA"
    try:
        residuo_final = abs(evaluar(f, aprox))
    except (ErrorDominio, ErrorNoFinito):
        residuo_final = float('nan')
    return ResultadoBiseccion(
        estado=estado, mensaje=f"Bisección finalizada por {motivo}.",
        aproximacion=aprox, intervalo_final=(a, b), E=entrada.error_absoluto,
        cota=cota_final, iteraciones=tuple(iteraciones), motivo_parada=motivo,
        metricas={"iteraciones_totales": len(iteraciones), "residuo_final": residuo_final}
    )