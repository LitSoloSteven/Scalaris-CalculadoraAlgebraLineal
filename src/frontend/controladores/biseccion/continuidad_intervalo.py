"""Adapta una captura parcial a la consulta de continuidad del dominio."""
from src.backend.resolutores.raices.diagnostico_biseccion import analizar_continuidad_intervalo
from .captura_criterio import real_capturado


def consultar_continuidad(captura: dict) -> dict:
    """Devuelve el informe o una indicación de captura inválida sin exigir criterio."""
    try:
        intervalo = (
            real_capturado(captura["extremo_izquierdo"], "El extremo a"),
            real_capturado(captura["extremo_derecho"], "El extremo b"),
        )
        cero = captura.get("cero_preferido")
        if cero is not None:
            cero = real_capturado(cero, "El cero elegido")
        return {"informe": analizar_continuidad_intervalo(
            captura["expresion"], intervalo, unidad_angular=captura["unidad_angular"], cero_preferido=cero)}
    except ValueError as error:
        return {"mensaje": str(error)}
