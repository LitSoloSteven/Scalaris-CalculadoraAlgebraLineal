"""Renderizado común de la vista previa cuadrada mediante un presentador."""
import json
import logging
from collections.abc import Callable

from nicegui import ui
from src.frontend.textos import VISTA_PREVIA_ERROR

registro = logging.getLogger(__name__)


async def actualizar_vista_previa(vista, panel, presentador: Callable) -> None:
    """Dibuja los bloques saneados del presentador en un contenedor aún montado."""
    contenedor = vista.contenedor_vista_previa
    if contenedor is None or contenedor.is_deleted:
        return
    contenedor.clear()
    try:
        resultado = presentador(panel.obtener_datos_matriz(), panel.dimension)
        with contenedor:
            if resultado['estado'] == 'limite':
                ui.label(resultado['mensaje']).classes('texto-secundario text-sm text-center sesion-numero')
                return
            for identificador, formula in resultado['bloques']:
                ui.html(f'<div id="{identificador}" class="matematicas-desplazamiento matematicas-etiqueta text-lg mb-4 w-full text-center">$$ {formula} $$</div>')
            ui.run_javascript(f"window.scalaris.renderizarMathJax({json.dumps(resultado['identificadores'])});")
    except Exception:
        registro.warning('No se pudo actualizar la vista previa matricial')
        if not contenedor.is_deleted:
            contenedor.clear()
            with contenedor:
                ui.label(VISTA_PREVIA_ERROR).classes('texto-secundario text-sm text-center sesion-numero')
