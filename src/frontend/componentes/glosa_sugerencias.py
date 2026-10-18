"""Chips interactivos de sugerencias, preguntas de seguimiento y botón de explicación."""
from __future__ import annotations

import html
from typing import Any, Callable
from nicegui import ui


def _es_evento_teclado(evento: Any) -> bool:
    """Determina si un evento de interacción fue originado por teclado verificando detail."""
    argumentos = getattr(evento, "args", evento)
    if isinstance(argumentos, dict):
        return argumentos.get("detail") == 0
    if isinstance(argumentos, (int, float)):
        return argumentos == 0
    if isinstance(argumentos, (list, tuple)) and len(argumentos) > 0:
        primer_elemento = argumentos[0]
        if isinstance(primer_elemento, dict):
            return primer_elemento.get("detail") == 0
        return primer_elemento == 0
    return False


def renderizar_fila_sugerencias(sugerencias: Any, al_elegir: Callable, *, variante: str = "panel_lateral", deshabilitado: bool = False):
    """Renderiza la fila horizontal o bloque de preguntas sugeridas."""
    clase_contenedor = "glosa-sugerencias" + (" glosa-sugerencias-en-linea" if variante == "en_linea" else "")
    if deshabilitado:
        clase_contenedor += " glosa-sugerencias-deshabilitado"

    contenedor = ui.element("div").classes(clase_contenedor).props(
        'role="group" aria-label="Preguntas sugeridas"'
    )
    if deshabilitado:
        contenedor.props('aria-disabled="true"')

    botones = []
    with contenedor:
        for sugerencia in sugerencias:
            boton = _crear_boton_sugerencia(sugerencia, al_elegir, variante=variante, deshabilitado=deshabilitado)
            botones.append(boton)

    return contenedor, botones


def _crear_boton_sugerencia(sugerencia: Any, al_elegir: Callable, *, variante: str, deshabilitado: bool) -> ui.element:
    """Construye una cápsula individual con su manejador de evento."""
    clase_boton = "glosa-sugerencia" + (" glosa-sugerencia-en-linea" if variante == "en_linea" else "")
    boton = ui.element("button").classes(clase_boton).props('type="button"')
    with boton:
        ui.html(f'<span class="glosa-sugerencia-texto">{html.escape(sugerencia.texto)}</span>')

    if deshabilitado:
        boton.props('disabled aria-disabled="true"')

    def manejador(evento):
        """Atiende el evento del control y actualiza su estado."""
        al_elegir(sugerencia, _es_evento_teclado(evento))

    boton.on("click", manejador, args=["detail"])
    return boton


def renderizar_seguimientos(seguimientos: Any, al_elegir: Callable, *, deshabilitado: bool = False):
    """Renderiza las alternativas de seguimiento didáctico tras una respuesta."""
    clase_contenedor = "glosa-seguimientos w-full mt-2" + (" glosa-sugerencias-deshabilitado" if deshabilitado else "")
    contenedor = ui.element("div").classes(clase_contenedor).props(
        'role="group" aria-label="Seguimientos" aria-live="off"'
    )
    if deshabilitado:
        contenedor.props('aria-disabled="true"')

    botones = []
    with contenedor:
        for seguimiento in seguimientos:
            boton = ui.element("button").classes("glosa-seguimiento").props('type="button"')
            with boton:
                ui.html(f'<span class="glosa-sugerencia-texto">{html.escape(seguimiento.etiqueta)}</span>')

            if deshabilitado:
                boton.props('disabled aria-disabled="true"')

            def manejador(evento, seguimiento_elegido=seguimiento):
                """Atiende el evento del control y actualiza su estado."""
                al_elegir(seguimiento_elegido, _es_evento_teclado(evento))

            boton.on("click", manejador, args=["detail"])
            botones.append(boton)

    return contenedor, botones


def renderizar_boton_explicacion(indice_paso: int, total_pasos: int, operacion: str, al_pulsar: Callable, *, esta_cargando: bool = False) -> ui.button | None:
    """Renderiza el botón accesible 'Explicar paso' para un paso algebraico concreto."""
    from src.frontend import banderas
    from src.frontend.sugerencias import glosa_configurada
    from src.frontend.componentes.iconos import icono_svg

    if not banderas.panel_lateral_habilitado():
        return None

    configurado = glosa_configurada()
    with ui.button(color=None).classes("glosa-boton-explicacion").props(
        f'aria-label="Explicar paso {indice_paso}" round flat ripple=false'
    ) as boton:
        ui.html(icono_svg("explicar_paso"))

    boton.tooltip("Explicar este paso" if configurado else "Glosa no está configurada")
    if esta_cargando or not configurado:
        boton.props("disabled")
        if esta_cargando:
            boton.classes("esta-cargando")
        return boton

    def manejador(evento):
        """Atiende el evento del control y actualiza su estado."""
        if _es_evento_teclado(evento):
            ui.run_javascript(
                "document.documentElement.setAttribute('data-glosa-instantaneo', 'true'); "
                "setTimeout(() => document.documentElement.removeAttribute('data-glosa-instantaneo'), 100);"
            )
        al_pulsar(indice_paso)

    boton.on("click", manejador, args=["detail"])
    return boton


def renderizar_capsula_foco(texto: str, al_quitar: Callable) -> ui.element:
    """Presenta el foco activo como cápsula en la cabecera del panel lateral."""
    capsula = ui.element("div").classes("glosa-foco-explicacion").props(f'title="{html.escape(texto)}"')
    with capsula:
        ui.icon("center_focus_strong").classes("glosa-foco-explicacion-icono")
        ui.label(texto).classes("glosa-foco-explicacion-texto")
        ui.button(icon="close", color=None, on_click=al_quitar).classes(
            "glosa-foco-explicacion-cerrar"
        ).props('round flat size=xs ripple=false aria-label="Quitar foco"').tooltip("Quitar foco")
    return capsula
