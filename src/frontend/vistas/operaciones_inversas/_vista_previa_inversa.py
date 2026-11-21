"""Adaptación de la captura de Inversa al renderizador matricial compartido."""
from src.frontend.controladores.algebra.operaciones_inversas.calculo.vista_previa import preparar_presentacion_previa
from src.frontend.vistas.compartido.vista_previa_matricial import actualizar_vista_previa as actualizar_previa_matricial


async def actualizar_vista_previa(vista) -> None:
    """Dibuja A y [A | I] usando el presentador de Inversa."""
    await actualizar_previa_matricial(vista, vista.panel_matriz_cuadrada, preparar_presentacion_previa)
