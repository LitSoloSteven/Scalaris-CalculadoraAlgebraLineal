"""Presentación de suboperaciones y detalle diferido de matrices."""
from nicegui import ui
from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor
from src.frontend.componentes.reproductor_pasos import renderizar_latex


def renderizar_cuerpo_matrices(paso: PasoReproductor, contenedor) -> None:
    """Pinta la operación, la fila simbólica/resultado y el detalle celda a celda."""
    datos_paso = paso.cuerpo or {}
    with contenedor:
        operacion_latex = datos_paso.get("representacion_operacion") or f"\\text{{Paso {paso.indice + 1}}}"
        with ui.row().classes('w-full items-center justify-center py-2'):
            renderizar_latex(operacion_latex)

        simbolica = datos_paso.get("matriz_simbolica_latex")
        resultado = datos_paso.get("matriz_resultado_latex")
        with ui.row().classes('w-full items-center justify-center gap-4 py-3 flex-wrap'):
            if simbolica:
                renderizar_latex(simbolica)
            if simbolica and resultado:
                ui.icon('arrow_forward', size='md').classes('texto-secundario')
            if resultado:
                renderizar_latex(resultado)

        pasos_celdas = datos_paso.get("pasos_celda_a_celda")
        if pasos_celdas:
            with ui.expansion('Ver detalle celda a celda', icon='visibility').classes(
                'w-full mt-2 pasos-expansion'
            ).props('header-class="font-medium texto-secundario"') as expansion:
                contenedor_detalle = ui.column().classes('w-full py-1')
                cargado = False

                def cargar_detalle(evento, celdas=pasos_celdas, destino=contenedor_detalle):
                    """Carga el detalle una sola vez al abrir la expansión."""
                    nonlocal cargado
                    if not evento.value or cargado:
                        return
                    cargado = True
                    _renderizar_detalles_celdas(celdas, destino)

                expansion.on_value_change(cargar_detalle)


def _renderizar_detalles_celdas(pasos_celdas, contenedor):
    """Muestra los detalles LaTeX de las celdas en su contenedor diferido."""
    with contenedor:
        for paso_celda in pasos_celdas:
            detalle = paso_celda.get("detalle_latex")
            if detalle:
                renderizar_latex(detalle)
