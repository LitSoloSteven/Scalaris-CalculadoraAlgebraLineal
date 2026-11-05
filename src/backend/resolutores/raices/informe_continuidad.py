"""Traducción de observaciones del motor a la política de continuidad."""
from typing import cast

from .contrato_biseccion import CODIGO_DISCONTINUIDAD, ResultadoBiseccion
from .contrato_continuidad import EvidenciaContinuidad, InformeContinuidad, TipoEvidencia

_RESTRICCIONES = {"DOMINIO_INVALIDO", "SINGULARIDAD_DETECTADA"}
_MENSAJES = {
    "CONFIRMADA": "Continuidad confirmada en todo el intervalo cerrado.",
    "NO_VERIFICADA": "Continuidad no verificada.",
    "RESTRICCION_DETECTADA": "Se detectó una restricción en el intervalo.",
}


def crear_informe(intervalo: tuple[float, float], unidad: str, evidencia: tuple[EvidenciaContinuidad, ...],
                  admite_cero: bool) -> InformeContinuidad:
    """Determina la política usando observaciones del intervalo y la excepción del cero válido."""
    if any(dato["codigo"] in _RESTRICCIONES for dato in evidencia):
        estado, politica = "RESTRICCION_DETECTADA", "ADVERTIR" if admite_cero else "RECHAZAR"
    elif all(dato["tipo"] == "COBERTURA_ESTRUCTURAL" for dato in evidencia):
        estado, politica = "CONFIRMADA", "PERMITIR"
    else:
        estado, politica = "NO_VERIFICADA", "ADVERTIR"
    return cast(InformeContinuidad, dict(intervalo=intervalo, unidad_angular=unidad, evidencia=evidencia,
                                       estado=estado, politica=politica, mensaje=_MENSAJES[estado]))


def observacion(tipo: TipoEvidencia, codigo: str, intervalo: tuple[float, float], detalle: str,
                abscisa: float | None = None) -> EvidenciaContinuidad:
    """Construye una observación estructurada para un intervalo o una abscisa."""
    return EvidenciaContinuidad(tipo=tipo, codigo=codigo, intervalo=intervalo, abscisa=abscisa, detalle=detalle)


def incorporar_traza(informe: InformeContinuidad, resultado: ResultadoBiseccion) -> InformeContinuidad:
    """Incorpora la sospecha observada en la traza sin convertirla en restricción estructural."""
    diagnostico = resultado.diagnostico or {}
    sospecha = diagnostico.get("evidencia_discontinuidad")
    if sospecha is None:
        return informe
    detalle = ("Las magnitudes crecieron al reducir el intervalo; la traza sugiere una discontinuidad.")
    dato = observacion("SOSPECHA_TRAZA", CODIGO_DISCONTINUIDAD, sospecha["intervalo"], detalle)
    return crear_informe(informe["intervalo"], informe["unidad_angular"], (*informe["evidencia"], dato), False)
