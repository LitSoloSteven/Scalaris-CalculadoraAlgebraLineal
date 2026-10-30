"""Estado e interpretación del determinante exacto preparado por el controlador."""
from nicegui import ui

from src.backend.utilidades.formateadores import numero_a_latex, formatear_fraccion_texto
from src.frontend import textos
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex


def mostrar_tarjeta_determinante(resultado: dict) -> None:
    """Muestra distintivo, métricas y determinante, con aviso cuando es singular."""
    singular = resultado.get("es_singular", False)
    with ui.row().classes("items-center gap-2 px-4 py-2 mb-4 w-fit " + (
            "distintivo-advertencia" if singular else "distintivo-exito")):
        ui.icon("warning" if singular else "check_circle", size="sm")
        ui.label(textos.DETERMINANTES_ESTADO_SINGULAR if singular else
                 textos.DETERMINANTES_INVERTIBLE).classes("font-bold").props('role="status"')
    _mostrar_metricas(resultado)
    ui.label(textos.DETERMINANTES_VALOR.format(valor=formatear_fraccion_texto(
        resultado["determinante"]))).classes("determinante-valor texto-principal")
    renderizar_latex(r"\det(A) = " + numero_a_latex(resultado["determinante"]))
    if singular:
        ui.label(textos.DETERMINANTES_AVISO_SINGULAR).classes("texto-secundario").props('role="status"')


def _mostrar_metricas(resultado: dict) -> None:
    dimension = resultado.get("dimension") or resultado["traza"][0]["matriz"].filas
    nombres = {clave: nombre for clave, nombre, _ in textos.OPCIONES_METODOS_DETERMINANTES}
    with ui.row().classes("panel-tarjeta px-4 py-2 fuente-pequena items-center gap-4 flex-wrap mb-6 w-full"):
        ui.label(f"{dimension} × {dimension}").classes("font-bold texto-principal")
        ui.label(nombres.get(resultado["metodo"], resultado["metodo"])).classes("texto-principal")
        ui.label(textos.RESULTADO_CUENTA_PASOS.format(cantidad=len(resultado["traza"]))).classes("texto-secundario")
        ui.label(textos.RESULTADO_INTERCAMBIOS.format(cantidad=resultado.get("intercambios", 0))).classes("texto-secundario")
        ui.label(textos.RESULTADO_TIEMPO.format(segundos=resultado.get(
            "tiempo_transcurrido_segundos", 0))).classes("texto-secundario")


def mostrar_interpretacion_determinante() -> None:
    """Explica el vínculo entre determinante, dependencia y existencia de inversa."""
    with ui.expansion(textos.RESULTADO_INTERPRETACION, icon="help_outline").classes("w-full mt-6 panel-tarjeta"):
        ui.label(textos.DETERMINANTES_INTERPRETACION).classes("texto-secundario text-sm p-3")
