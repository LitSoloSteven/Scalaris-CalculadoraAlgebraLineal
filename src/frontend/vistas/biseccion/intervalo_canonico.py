"""Aplicación de extremos canónicos después de comprobar la vigencia del cálculo."""
from src.ai.huellas import calcular_huella
from .selector_criterio import actualizar_guia


def reflejar_intervalo(vista, respuesta: dict) -> str | None:
    """Refleja la normalización del dominio sin retirar el resultado y devuelve su nueva huella."""
    entrada = respuesta.get("entrada", {})
    if not entrada.get("intervalo_invertido"):
        return None
    cargando = vista._cargando_captura
    vista._cargando_captura = True
    try:
        vista.inferior.set_value(str(entrada["extremo_izquierdo"]))
        vista.superior.set_value(str(entrada["extremo_derecho"]))
    finally:
        vista._cargando_captura = cargando
    actualizar_guia(vista)
    return calcular_huella(vista.capturar())
