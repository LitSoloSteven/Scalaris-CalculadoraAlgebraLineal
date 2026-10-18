"""Actualización cancelable de la vista previa matricial y su marcado MathJax."""
import json
import logging

from nicegui import ui

from src.frontend.controladores.operaciones_inversas.vista_previa import preparar_presentacion_previa

registro = logging.getLogger(__name__)


async def actualizar_vista_previa(vista) -> None:
    """Dibuja A y su aumentada tras la espera, si el contenedor sigue montado."""
    if not vista.contenedor_vista_previa or vista.contenedor_vista_previa.is_deleted:
        return
    try:
        vista.contenedor_vista_previa.clear()
        with vista.contenedor_vista_previa:
            dimension = vista.panel_matriz_cuadrada.dimension
            datos = vista.panel_matriz_cuadrada.obtener_datos_matriz()
            resultado = preparar_presentacion_previa(datos, dimension)
            if resultado['estado'] == 'limite':
                ui.label(resultado['mensaje']).classes(
                    'texto-secundario italic text-sm mt-4 text-center')
                return
            matriz_latex = resultado['matriz_latex']
            aumentada_latex = resultado['aumentada_latex']
            identificadores = resultado['identificadores']
            ui.html(f'<div id="inversa-previa-matriz" class="matematicas-desplazamiento matematicas-etiqueta text-lg mb-4 w-full text-center">$$ A = {matriz_latex} $$</div>')
            if aumentada_latex:
                ui.html(rf'<div id="inversa-previa-aumentada" class="matematicas-desplazamiento matematicas-etiqueta text-base w-full text-center">$$ [A \mid I] = {aumentada_latex} $$</div>')
            ui.run_javascript(f"window.scalaris.renderizarMathJax({json.dumps(identificadores)});")
    except Exception:
        if not vista.contenedor_vista_previa or vista.contenedor_vista_previa.is_deleted:
            return
        registro.exception("Error al actualizar vista previa de matriz inversa")
        with vista.contenedor_vista_previa:
            ui.label('No se pudo generar la vista previa.').classes('texto-secundario italic text-sm mt-4 text-center')
