"""Construcción de trazas y cierres finitos con diagnósticos de bisección."""
import math
from collections.abc import Sequence

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from .aritmetica_biseccion import ancho_intervalo, cota_intervalo, error_relativo_numerico
from .contrato_biseccion import EntradaBiseccion, IteracionBiseccion, ResultadoBiseccion

_CIERRES = {
    "ancho_menor_que_E": ("EXITO", "CONVERGENCIA_POR_ANCHO", "El ancho del intervalo es menor que la tolerancia solicitada."),
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
        explicacion=_explicar_particion(extremos, medio),
    )


def construir_resultado(entrada: EntradaBiseccion, intervalo: tuple[float, float], iteraciones: Sequence[IteracionBiseccion], motivo: str, muestra: tuple[float, float]) -> ResultadoBiseccion:
    """Devuelve un cierre coherente con la última muestra, sin reevaluar ni cambiar intervalo."""
    estado, codigo, mensaje = _CIERRES[motivo]
    return ResultadoBiseccion(
        estado=estado, mensaje=mensaje, aproximacion=muestra[0], intervalo_final=intervalo,
        error_absoluto=entrada.error_absoluto, cota=cota_intervalo(*intervalo),
        iteraciones=tuple(iteraciones), motivo_parada=motivo, codigo_diagnostico=codigo,
        metricas={"iteraciones_totales": len(iteraciones), "residuo_final": abs(muestra[1]),
                  "continuidad": "La garantía requiere continuidad en todo el intervalo; el análisis estructural no es una certificación general."},
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


def _explicar_particion(extremos: tuple, medio: tuple) -> str:
    inferior, superior, valor_inferior, _ = extremos
    abscisa, valor_medio = medio
    if valor_medio == 0:
        return "f(c) se evaluó como cero. Se detiene el cálculo sin certificar exactitud simbólica."
    if abscisa in (inferior, superior):
        return "El punto medio se redondea a un extremo. La representación numérica no permite reducir el intervalo."
    if math.copysign(1, valor_inferior) != math.copysign(1, valor_medio):
        return f"Se conserva [{inferior}, {abscisa}] porque f(a) y f(c) tienen signos opuestos."
    return f"Se conserva [{abscisa}, {superior}] porque f(c) y f(b) tienen signos opuestos."
