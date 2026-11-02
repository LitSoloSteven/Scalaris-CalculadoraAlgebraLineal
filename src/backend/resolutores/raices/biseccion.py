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
        fa = evaluar(f, entrada.extremo_izquierdo)
        fb = evaluar(f, entrada.extremo_derecho)
    except (ValueError, ErrorDominio, ErrorNoFinito) as error:
        return ResultadoBiseccion(estado="ERROR", mensaje=str(error))

    inicial = _validar_extremos(entrada, fa, fb)
    if inicial is not None:
        return inicial

    error_absoluto = entrada.error_absoluto
    extremo_izquierdo, extremo_derecho = entrada.extremo_izquierdo, entrada.extremo_derecho
    iteraciones, c_previo, motivo = [], None, ""

    for i in range(1, entrada.limite_iteraciones + 1):
        c = (extremo_izquierdo + extremo_derecho) / 2.0
        try:
            fc = evaluar(f, c)
        except (ErrorDominio, ErrorNoFinito) as error:
            return ResultadoBiseccion(estado="ERROR", mensaje=f"Error en iteración {i}: {error}", iteraciones=tuple(iteraciones))

        iteraciones.append(_crear_iteracion(i, c, fc, (extremo_izquierdo, extremo_derecho, fa, fb), c_previo))
        if fc == 0.0:
            motivo = "raiz_exacta"
            break
        if (extremo_derecho - extremo_izquierdo) < error_absoluto:
            motivo = "ancho_menor_que_E"
            break
        (extremo_izquierdo, fa), (extremo_derecho, fb) = _actualizar_intervalo((extremo_izquierdo, fa), (extremo_derecho, fb), (c, fc))
        c_previo = c
    else:
        motivo = "limite_iteraciones"

    return _construir_resultado((extremo_izquierdo, extremo_derecho), entrada, motivo, iteraciones, f)


def _validar_extremos(entrada: EntradaBiseccion, fa: float, fb: float) -> ResultadoBiseccion | None:
    """Detecta raíces exactas en los extremos o la ausencia de cambio de signo."""
    if fa == 0.0 or fb == 0.0:
        es_extremo_a = fa == 0.0
        return ResultadoBiseccion(
            estado="EXITO",
            mensaje=f"La raíz está exactamente en el extremo {'extremo_izquierdo' if es_extremo_a else 'extremo_derecho'}.",
            aproximacion=entrada.extremo_izquierdo if es_extremo_a else entrada.extremo_derecho,
            intervalo_final=(entrada.extremo_izquierdo, entrada.extremo_derecho),
            error_absoluto=entrada.error_absoluto,
            cota=(entrada.extremo_derecho - entrada.extremo_izquierdo) / 2.0,
            iteraciones=(),
            motivo_parada="raiz_exacta",
            metricas={"iteraciones_totales": 0, "residuo_final": 0.0}
        )
    if math.copysign(1.0, fa) == math.copysign(1.0, fb):
        return ResultadoBiseccion(
            estado="SIN_CAMBIO_DE_SIGNO",
            mensaje=f"f(extremo_izquierdo)={fa} y f(extremo_derecho)={fb} tienen el mismo signo."
        )
    return None


def _crear_iteracion(i: int, c: float, fc: float, estado: tuple[float, float, float, float], c_previo: float | None) -> IteracionBiseccion:
    """Construye el registro inmutable de una iteración."""
    extremo_izquierdo, extremo_derecho, fa, fb = estado
    return IteracionBiseccion(
        i=i, extremo_izquierdo=extremo_izquierdo, extremo_derecho=extremo_derecho, c=c, f_a=fa, f_b=fb, f_c=fc,
        ancho=extremo_derecho - extremo_izquierdo, cota=(extremo_derecho - extremo_izquierdo) / 2.0, residuo=abs(fc),
        error_relativo=_calcular_error_relativo(c, c_previo),
        explicacion=_explicar_intervalo(extremo_izquierdo, extremo_derecho, c, fa, fc)
    )


def _calcular_error_relativo(c: float, c_previo: float | None) -> str:
    if c_previo is None or c == 0:
        return "No aplica"
    return f"{abs((c - c_previo) / c) * 100:.2f}%"


def _explicar_intervalo(extremo_izquierdo: float, extremo_derecho: float, c: float, fa: float, fc: float) -> str:
    if math.copysign(1.0, fa) != math.copysign(1.0, fc):
        return f"Se conserva [{extremo_izquierdo}, {c}] porque f(extremo_izquierdo) y f(c) tienen signos opuestos."
    return f"Se conserva [{c}, {extremo_derecho}] porque f(c) y f(extremo_derecho) tienen signos opuestos."


def _actualizar_intervalo(inferior: tuple[float, float], superior: tuple[float, float], medio: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    """Conserva el subintervalo que encierra la raíz y devuelve los extremos y sus valores."""
    extremo_izquierdo, fa = inferior
    extremo_derecho, fb = superior
    c, fc = medio
    if math.copysign(1.0, fa) != math.copysign(1.0, fc):
        return (extremo_izquierdo, fa), (c, fc)
    return (c, fc), (extremo_derecho, fb)


def _construir_resultado(intervalo: tuple[float, float], entrada: EntradaBiseccion, motivo: str, iteraciones: list, f) -> ResultadoBiseccion:
    extremo_izquierdo, extremo_derecho = intervalo
    aprox = (extremo_izquierdo + extremo_derecho) / 2.0
    cota_final = (extremo_derecho - extremo_izquierdo) / 2.0
    estado = "EXITO" if motivo != "limite_iteraciones" else "PRECISION_NO_ALCANZADA"
    try:
        residuo_final = abs(evaluar(f, aprox))
    except (ErrorDominio, ErrorNoFinito):
        residuo_final = float('nan')
    return ResultadoBiseccion(
        estado=estado, mensaje=f"Bisección finalizada por {motivo}.",
        aproximacion=aprox, intervalo_final=(extremo_izquierdo, extremo_derecho), error_absoluto=entrada.error_absoluto,
        cota=cota_final, iteraciones=tuple(iteraciones), motivo_parada=motivo,
        metricas={"iteraciones_totales": len(iteraciones), "residuo_final": residuo_final}
    )