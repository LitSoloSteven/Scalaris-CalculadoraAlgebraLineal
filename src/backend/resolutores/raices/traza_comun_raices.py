"""Helpers de traza compartidos por los motores de raices (biseccion y regla falsa)."""
from dataclasses import replace


def registrar_accion(fila, motivo: str, mensajes: dict):
    """Registra el cierre o el reemplazo de extremo que ejecutara el motor."""
    if motivo:
        return replace(fila, accion="detener", motivo_parada=motivo, explicacion=mensajes[motivo][2])
    if fila.signo_producto == -1:
        return replace(
            fila, accion="reemplazar_b",
            explicacion=f"Se conserva [{fila.extremo_izquierdo}, {fila.c}] porque f(a) y f(c) tienen signos opuestos.",
        )
    return replace(
        fila, accion="reemplazar_a",
        explicacion=f"Se conserva [{fila.c}, {fila.extremo_derecho}] porque f(c) y f(b) tienen signos opuestos.",
    )
    
def texto_error_relativo(abscisa: float, previo: float | None, relativo: float | None) -> str:
    """Devuelve 'No aplica', 'No representable' o el porcentaje con dos decimales."""
    texto = "No aplica" if previo is None or abscisa == 0 else "No representable"
    if relativo is not None:
        texto = f"{relativo:.2f}%"
    return texto