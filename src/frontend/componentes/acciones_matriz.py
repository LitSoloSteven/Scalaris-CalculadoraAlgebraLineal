"""Acciones de navegación que conservan la matriz del cálculo publicado."""
from functools import partial
from nicegui import ui

from src.frontend import textos
from src.frontend.componentes.transferencia import guardar_matriz, url_transferencia
from src.frontend.controladores.destinos_matriz import destinos_compatibles
from src.frontend.navegacion import herramienta_por_identificador, ruta_de


def _llevar_matriz(origen: str, datos: list[list[str]], destino: str, vigente=None) -> None:
    if vigente is not None and not vigente():
        return
    token = guardar_matriz(origen, datos)
    ui.navigate.to(url_transferencia(ruta_de(destino), token))


def renderizar_acciones_matriz(origen: str, datos: list[list[str]], *, vigente=None) -> None:
    """Ofrece destinos compatibles con una copia de la matriz del cálculo,
    conservada aunque el editor cambie después."""
    if not datos or not datos[0] or origen == "vectores":
        return
    filas, columnas = len(datos), len(datos[0])
    destinos = destinos_compatibles(filas, columnas, origen)
    if not destinos:
        return
    captura = [[valor or "0" for valor in fila] for fila in datos]
    with ui.column().classes("w-full min-w-0 gap-2"):
        ui.label(textos.TRANSFERENCIA_MATRIZ_TITULO).classes("font-semibold texto-principal")
        with ui.row().classes("w-full gap-2 flex-wrap").props(
            f'role="group" aria-label="{textos.TRANSFERENCIA_MATRIZ_TITULO}"'
        ):
            for destino in destinos:
                ui.button(herramienta_por_identificador(destino).nombre, color=None,
                          on_click=partial(_llevar_matriz, origen, captura, destino, vigente)).classes(
                    "boton-discreto max-w-full").props(f'ripple=false data-destino-matriz="{destino}"')
