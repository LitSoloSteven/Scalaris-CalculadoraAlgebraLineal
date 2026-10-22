"""Adaptación de la captura de Inversa al renderizador matricial compartido."""
from src.frontend.controladores.operaciones_inversas.vista_previa import preparar_presentacion_previa
from src.frontend.vistas.vista_previa_matricial import actualizar_vista_previa as actualizar_previa_matricial


async def actualizar_vista_previa(vista) -> None:
    """Dibuja A y [A | I] usando el presentador de Inversa."""
    await actualizar_previa_matricial(vista, vista.panel_matriz_cuadrada, preparar_presentacion_previa)
