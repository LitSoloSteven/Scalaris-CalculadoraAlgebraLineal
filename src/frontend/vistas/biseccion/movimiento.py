"""Enlace entre la modalidad del envío y las entradas visuales vigentes."""
import json

from nicegui import ui

REGISTRAR_ENTRADA = "evento => window.scalaris.movimientoBiseccion.registrarEntrada(evento)"


def vincular_envio(nodo, accion) -> None:
    """Envía la modalidad de la activación junto al clic."""
    nodo.on("click", accion, js_handler="evento => emit(evento.detail > 0)")


def modalidad_puntero(evento) -> bool | None:
    """Interpreta clics físicos y devuelve None si no hay un evento de navegador."""
    datos = getattr(evento, "args", None)
    return datos if isinstance(datos, bool) else None


def animar_entrada(nodo, puntero: bool) -> None:
    """Anima el nodo publicado cuando el envío se hizo con puntero."""
    if puntero:
        ui.run_javascript(
            f"window.scalaris.movimientoBiseccion?.entrada(document.getElementById('{nodo.html_id}'), true)"
        )


def cancelar_entrada(nodo) -> None:
    """Retira la animación antes de vaciar una región persistente."""
    if not nodo.is_deleted:
        ui.run_javascript(
            f"window.scalaris.movimientoBiseccion?.cancelar(document.getElementById('{nodo.html_id}'))"
        )


def publicar_formula(identificador: str, preparado: dict) -> None:
    """Traslada al paso visible la fórmula ya compuesta para esa revisión."""
    ui.run_javascript(
        f"window.scalaris.pasoBiseccion.publicar({json.dumps(dict(preparado, identificador=identificador))})"
    )
