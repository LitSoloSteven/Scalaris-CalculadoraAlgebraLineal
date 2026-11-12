"""Presentación compartida de evidencia y política de continuidad del dominio."""
from nicegui import ui


def mostrar_informe_continuidad(informe: dict, clase_numero: str) -> None:
    """Presenta un informe mediante texto escapado conservando los estilos del consumidor."""
    inferior, superior = informe["intervalo"]
    ui.label(f'{informe["mensaje"]} [{inferior:.17g}, {superior:.17g}]').classes(clase_numero)
    if informe["politica"] == "RECHAZAR":
        ui.label("Revisa la función o los extremos del intervalo.").classes("texto-advertencia")
    for dato in informe["evidencia"]:
        ubicacion = f' En x = {dato["abscisa"]:.17g}.' if dato["abscisa"] is not None else ""
        ui.label(dato["detalle"] + ubicacion).classes("text-sm texto-secundario")
