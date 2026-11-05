"""Construcción de trazas y cierres finitos con diagnósticos de bisección."""
from collections.abc import Sequence
from dataclasses import replace

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from .aritmetica_biseccion import ancho_intervalo, cota_intervalo, error_relativo_numerico
from .contrato_biseccion import CONTINUIDAD_CONDICIONAL, EntradaBiseccion, IteracionBiseccion, ResultadoBiseccion
from .decision_biseccion import signo_producto

_CIERRES = {
    "ancho_menor_que_E": ("EXITO", "CONVERGENCIA_POR_ANCHO", "El ancho del intervalo es menor que la tolerancia solicitada."),
    "relativo_menor_que_porcentaje": ("EXITO", "CONVERGENCIA_POR_RELATIVO", "El error relativo aproximado es menor que el porcentaje solicitado."),
    "residuo_menor_que_delta": ("EXITO", "CONVERGENCIA_POR_RESIDUO", "El residuo es menor que la tolerancia solicitada; no es una cota del error en x."),
    "iteraciones_completadas": ("ITERACIONES_COMPLETADAS", "ITERACIONES_COMPLETADAS", "Se completó el número fijo de iteraciones; esto no implica convergencia por tolerancia."),
    "raiz_exacta": ("EXITO", "CERO_EVALUADO", "La función se evaluó como cero en aritmética aproximada; esto no certifica exactitud simbólica."),
    "estancamiento": ("PRECISION_NO_ALCANZADA", "ESTANCAMIENTO", "El punto medio coincide con un extremo por límites de representación. No se alcanzó la precisión solicitada."),
    "limite_iteraciones": ("PRECISION_NO_ALCANZADA", "LIMITE_ITERACIONES", "Se alcanzó el límite de iteraciones sin cumplir la precisión solicitada."),
}


def crear_iteracion(indice: int, extremos: tuple[float, float, float, float], medio: tuple[float, float], previo: float | None) -> IteracionBiseccion:
    """Construye una iteración con métricas finitas y error relativo numérico compatible."""
    inferior, superior, valor_inferior, valor_superior = extremos
    abscisa, valor_medio = medio
    relativo = error_relativo_numerico(abscisa, previo)
    texto = "No aplica" if previo is None or abscisa == 0 else "No representable"
    if relativo is not None:
        texto = f"{relativo:.2f}%"
    return IteracionBiseccion(
        i=indice, extremo_izquierdo=inferior, extremo_derecho=superior, c=abscisa,
        f_a=valor_inferior, f_b=valor_superior, f_c=valor_medio,
        ancho=ancho_intervalo(inferior, superior), cota=cota_intervalo(inferior, superior),
        residuo=abs(valor_medio), error_relativo=texto, error_relativo_valor=relativo,
        explicacion="", signo_producto=signo_producto(valor_inferior, valor_medio),
    )


def registrar_accion(fila: IteracionBiseccion, motivo: str) -> IteracionBiseccion:
    """Registra el cierre o el reemplazo de extremo que ejecutará el motor."""
    if motivo:
        explicacion = _CIERRES[motivo][2]
        if motivo == "estancamiento":
            explicacion = "El punto medio se redondea a un extremo. La representación numérica no permite reducir el intervalo."
        return replace(fila, accion="detener", motivo_parada=motivo, explicacion=explicacion)
    if fila.signo_producto == -1:
        return replace(fila, accion="reemplazar_b",
                       explicacion=f"Se conserva [{fila.extremo_izquierdo}, {fila.c}] porque f(a) y f(c) tienen signos opuestos.")
    return replace(fila, accion="reemplazar_a",
                   explicacion=f"Se conserva [{fila.c}, {fila.extremo_derecho}] porque f(c) y f(b) tienen signos opuestos.")


def construir_resultado(entrada: EntradaBiseccion, intervalo: tuple[float, float], iteraciones: Sequence[IteracionBiseccion], motivo: str, muestra: tuple[float, float]) -> ResultadoBiseccion:
    """Devuelve un cierre coherente con la última muestra, sin reevaluar ni cambiar intervalo."""
    estado, codigo, mensaje = _CIERRES[motivo]
    return ResultadoBiseccion(
        estado=estado, mensaje=mensaje, aproximacion=muestra[0], intervalo_final=intervalo,
        error_absoluto=entrada.error_absoluto, cota=cota_intervalo(*intervalo),
        iteraciones=tuple(iteraciones), motivo_parada=motivo, codigo_diagnostico=codigo,
        metricas={"iteraciones_totales": len(iteraciones), "residuo_final": abs(muestra[1]),
                  "continuidad": CONTINUIDAD_CONDICIONAL},
    )


def construir_error(error: ValueError, iteraciones: Sequence[IteracionBiseccion] = (), codigo: str = "EXPRESION_INVALIDA") -> ResultadoBiseccion:
    """Conserva la traza válida y clasifica el error sin publicar aproximaciones no fiables."""
    if isinstance(error, ErrorNoFinito):
        codigo = "EVALUACION_NO_FINITA"
    elif isinstance(error, ErrorDominio):
        codigo = "DOMINIO_INVALIDO"
    return ResultadoBiseccion(estado="ERROR", mensaje=str(error), iteraciones=tuple(iteraciones),
                              motivo_parada="evaluacion_invalida", codigo_diagnostico=getattr(error, "codigo", codigo),
                              metricas={"iteraciones_totales": len(iteraciones)})
