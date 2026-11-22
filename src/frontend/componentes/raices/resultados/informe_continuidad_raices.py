"""Presentación compartida de evidencia y política de continuidad del dominio."""
from nicegui import ui
from src.frontend.controladores.raices.compartido.formato.formato_numerico_raices import numero


def mostrar_informe_continuidad(informe: dict, clase_numero: str) -> None:
    """Presenta un informe mediante texto escapado conservando los estilos del consumidor."""
    inferior, superior = informe["intervalo"]
    ui.label(f'{informe["mensaje"]} [{inferior:.17g}, {superior:.17g}]').classes(clase_numero)
    if informe["politica"] == "RECHAZAR":
        ui.label("Revisa la función o los extremos del intervalo.").classes("texto-advertencia")
    for dato in informe["evidencia"]:
        ubicacion = f' En x = {dato["abscisa"]:.17g}.' if dato["abscisa"] is not None else ""
        ui.label(dato["detalle"] + ubicacion).classes("text-sm texto-secundario")


def mostrar_consulta_continuidad(respuesta: dict, clase_informe: str, clase_evaluacion: str,
                                mensaje: str | None = None) -> None:
    """Presenta el informe previo, evaluaciones y el aviso de la consulta vigente."""
    if respuesta.get("informe") is not None:
        mostrar_informe_continuidad(respuesta["informe"], clase_informe)
        for evaluacion in respuesta.get("evaluaciones", ()):
            valor = evaluacion["mensaje"] if evaluacion["codigo"] else numero(evaluacion["valor"], True)
            ui.label(f"f({numero(evaluacion['abscisa'], True)}) = {valor}").classes(clase_evaluacion)
    aviso = mensaje or (respuesta.get("fallo") or {}).get("mensaje")
    if aviso:
        ui.label(aviso).classes("texto-advertencia text-sm")
