"""Controles compartidos de captura para modelos matriciales."""
from typing import Any
from nicegui import ui
from .cuadricula_base import propiedades_celda_accesible
from .carga_numerica import preparar_matriz_numerica


def crear_entradas_vector(contenedor: Any, cantidad: int, identificador: str) -> list[Any]:
    """Devuelve controles de un vector fila con coordenadas de pegado y nombres accesibles."""
    valores = [entrada.value for entrada in contenedor.descendants() if isinstance(entrada, ui.input)]
    entradas = []
    contenedor.clear()
    with contenedor, ui.row().classes("gap-2 flex-nowrap"):
        for indice in range(cantidad):
            entrada = ui.input(value=valores[indice] if indice < len(valores) else "", placeholder="0", label=f"d{indice + 1}").classes("matriz-entrada w-20 shrink-0")
            entrada.props(propiedades_celda_accesible(0, indice, identificador_matriz=identificador))
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
            entrada = ui.input(value=valores[indice] if indice < len(valores) else "", placeholder=nombre, label=nombre).classes("matriz-entrada w-28 min-w-0")
            entrada.props(propiedades_celda_accesible(0, indice, identificador_matriz=etiqueta, solo_numerico=False))
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


def construir_ejemplos(ejemplos: list[dict], cargar: Any, titulo: str) -> None:
    """Monta botones de ejemplos internos; cargar recibe el diccionario seleccionado."""
    from functools import partial
    with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
        ui.label(titulo).classes("font-bold texto-principal mb-2 text-sm uppercase tracking-wide")
        with ui.row().classes("gap-2 flex-wrap"):
            for ejemplo in ejemplos:
                ui.button(ejemplo["nombre"], on_click=partial(cargar, ejemplo), color=None).classes(
                    "boton-discreto text-xs py-1 px-3"
                ).props("ripple=false").tooltip(ejemplo["descripcion"])
