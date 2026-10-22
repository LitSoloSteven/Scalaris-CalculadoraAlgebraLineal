"""Delegación de la preparación matemática de la vista previa de inversa."""
from src.backend.resolutores.operaciones_matrices.vista_previa_inversa import generar_latex_vista_previa
from src.frontend.controladores.vista_previa_matricial import orientacion_limite_previa


def preparar_vista_previa_inversa(datos: list[list[str]], dimension: int) -> tuple[str, str | None, list[str]]:
    """Devuelve los bloques LaTeX y sus identificadores serializables."""
    return generar_latex_vista_previa(datos, dimension)


def preparar_presentacion_previa(datos: list[list[str]], dimension: int) -> dict:
    """Devuelve el estado, orientacion y bloques listos para presentar la captura."""
    limite = orientacion_limite_previa(dimension)
    if limite:
        return limite
    matriz, aumentada, identificadores = preparar_vista_previa_inversa(datos, dimension)
    bloques = [('inversa-previa-matriz', f'A = {matriz}')]
    if aumentada:
        bloques.append(('inversa-previa-aumentada', rf'[A \mid I] = {aumentada}'))
    return {'estado': 'exito', 'matriz_latex': matriz, 'aumentada_latex': aumentada,
            'identificadores': identificadores, 'bloques': bloques}
