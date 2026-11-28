"""Controles compartidos de captura para modelos matriciales."""
from typing import Any
from nicegui import ui
from src.frontend.componentes.captura.nucleo.cuadricula_base import propiedades_celda_accesible
from src.frontend.componentes.captura.nucleo.carga_numerica import preparar_matriz_numerica


def crear_entradas_vector(contenedor: Any, cantidad: int, identificador: str) -> list[Any]:
    """Devuelve controles de un vector fila con coordenadas de pegado y nombres accesibles."""
    valores = [entrada.value for entrada in contenedor.descendants() if isinstance(entrada, ui.input)]
    entradas = []
    contenedor.clear()
    with contenedor, ui.column().classes("cuadricula-contenido w-full"), ui.row().classes("gap-2 no-wrap w-full"):
        for indice in range(cantidad):
            entrada = ui.input(value=valores[indice] if indice < len(valores) else "", label=f"d{indice + 1}").classes("matriz-entrada cuadricula-celda text-center")
            entrada.props(propiedades_celda_accesible(0, indice, identificador_matriz=identificador))
            etiqueta = f"Demanda final sector {indice + 1}" if identificador == "d" else f"Componente {identificador}{indice + 1}"
            entrada.props(f'aria-label="{etiqueta}"')
            entradas.append(entrada)
    return entradas


def crear_entradas_nombres(contenedor: Any, cantidad: int, etiqueta: str) -> list[Any]:
    """Devuelve campos opcionales de nombres con etiqueta y distribución adaptable."""
    valores = [entrada.value for entrada in contenedor.descendants() if isinstance(entrada, ui.input)]
    entradas = []
    contenedor.clear()
    with contenedor, ui.row().classes("gap-2 flex-wrap"):
        for indice in range(cantidad):
            nombre = f"{etiqueta} {indice + 1}"
            entrada = ui.input(
                value=valores[indice] if indice < len(valores) else "", label=nombre,
            ).classes("matriz-entrada modelos-campo-nombre min-w-0")
            entrada.props(propiedades_celda_accesible(0, indice, identificador_matriz=etiqueta, solo_numerico=False))
            entrada.props(f'aria-label="{nombre}"')
            entradas.append(entrada)
    return entradas


def llenar_entradas(entradas: list[Any], valores: list[str]) -> None:
    """Asigna datos de un ejemplo a controles ya montados y limpia posiciones sin datos."""
    cargados = [valores[indice] if indice < len(valores) else "" for indice in range(len(entradas))]
    numericos = [indice for indice, entrada in enumerate(entradas) if entrada._props.get("data-solo-numerico") == "true"]
    filtrados = preparar_matriz_numerica([[cargados[indice] for indice in numericos]])[0]
    for indice, valor in zip(numericos, filtrados):
        cargados[indice] = valor
    for entrada, valor in zip(entradas, cargados):
        entrada.value = valor
