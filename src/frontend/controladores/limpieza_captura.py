"""Operaciones de presentación para retirar una captura y su explicación."""
from src.backend.utilidades.estado_captura import captura_vacia
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto


def campos_vacios(entradas) -> bool:
    """Consulta presencia textual de controles, incluidos los ceros escritos."""
    return captura_vacia((entrada.value for entrada in entradas), considerar_cero=False)


def vaciar_campos(entradas) -> None:
    """Borra los valores de controles existentes sin alterar su estructura."""
    for entrada in entradas:
        entrada.set_value('')


def retirar_estado_calculado(vista) -> None:
    """Invalida resultado y huella, detiene reproductores y retira el foco de Glosa."""
    invalidar_resultado(vista)
    reproductor = getattr(vista, 'reproductor', None)
    if reproductor is not None:
        reproductor.detener()
        vista.reproductor = None
    panel = getattr(vista, 'panel_ia', None)
    if panel is not None:
        panel.limpiar_foco_explicacion()
    actualizar_contexto(vista)
