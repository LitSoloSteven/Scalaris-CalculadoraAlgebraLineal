"""Barra de navegación contextual y de acceso rápido para Scalaris."""
from __future__ import annotations

import html
import json
from typing import Any
from nicegui import ui


from src.frontend import banderas
from src.frontend.componentes.iconos import icono_svg
from src.frontend.componentes.selector_tema import renderizar_boton_tema
from src.frontend.componentes.accesos_algebra import renderizar_accesos_algebra
from src.frontend.navegacion import (
    RUTA_INICIO,
    ORDEN_NAVEGACION_PLANA,
    predeterminado_elemento_clave,
    enlace_elemento_navegacion,
    elementos_navegacion,
    pilar_por_ruta,
    herramienta_por_identificador,
    herramienta_por_ruta,
)


def crear_barra_navegacion(interfaz_activa=None, ruta_activa: str = "/", clave_activa: str | None = None, al_alternar_ia=None):
    """Genera la barra de navegación contextual plana o por pilares según banderas."""
    clave_activa = predeterminado_elemento_clave(ruta_activa) if clave_activa is None else clave_activa

    with ui.header().classes("navegacion-cabecera").props("reveal"):
        _renderizar_logotipo()
        with ui.element("div").classes("panel-tarjeta navegacion-capsula pointer-events-auto"):
            if not banderas.navegacion_actualizada():
                _renderizar_barra_plana(interfaz_activa, ruta_activa, al_alternar_ia)
            else:
                _renderizar_barra_pilares(ruta_activa, clave_activa)

    if banderas.navegacion_actualizada():
        _registrar_navegacion_reciente(ruta_activa)


def _renderizar_logotipo() -> None:
    """Renderiza el logotipo interactivo enlazado al inicio."""
    with ui.link(target="/").classes(
        "marca-enlace-logotipo marca-enlace-esquina pointer-events-auto select-none no-underline"
    ).props('aria-label="Scalaris - Inicio"').tooltip("Scalaris: Inicio"):
        ui.html(
            '<div class="marca-contenedor-logotipo flex items-center justify-center">'
            '<img src="/assets/LogoOscuro.png" alt="Scalaris" class="marca-logotipo marca-logotipo-oscuro" />'
            '<img src="/assets/LogoClaro.png" alt="Scalaris" class="marca-logotipo marca-logotipo-claro" />'
            '</div>'
        )


def _renderizar_barra_plana(interfaz_activa: Any, ruta_activa: str, al_alternar_ia=None) -> None:
    """Renderiza la botonera lineal de herramientas en modo clásico."""
    with ui.row().classes("items-center gap-4"):
        for identificador_herramienta in ORDEN_NAVEGACION_PLANA:
            herramienta = herramienta_por_identificador(identificador_herramienta)
            esta_activa = (ruta_activa == herramienta.ruta)
            pagina_actual = ' aria-current="page"' if esta_activa else ""
            propiedades = f'flat ripple=false href="{herramienta.ruta}" aria-label="{herramienta.nombre}"{pagina_actual}'
            clase = "boton-icono p-0" + (" navegacion-activa" if esta_activa else "")
            with ui.button(color=None).classes(clase).props(propiedades).tooltip(herramienta.nombre):
                ui.html(icono_svg(herramienta.icono))

        if not banderas.panel_lateral_habilitado():
            def alternar_ia():
                """Alterna el panel del asistente desde el control de navegación."""
                if interfaz_activa and hasattr(interfaz_activa, "panel_ia"):
                    interfaz_activa.panel_ia.alternar()

            with ui.button(on_click=al_alternar_ia or alternar_ia, color=None).classes(
                "boton-icono p-0 texto-principal"
            ).props('flat ripple=false aria-label="Glosa"').tooltip("Glosa"):
                ui.html(icono_svg("tutor_ia"))

        ui.element("div").classes("navegacion-separador")
        renderizar_boton_tema()


def _renderizar_barra_pilares(ruta_activa: str, clave_activa: str) -> None:
    """Renderiza la botonera contextual por pilares temáticos (v2)."""
    with ui.element("a").classes("navegacion-accion navegacion-inicio").props(
        f'href="{RUTA_INICIO}" aria-label="Inicio" title="Inicio"'
    ).tooltip("Inicio"):
        ui.html(icono_svg("inicio"))

    pilar = pilar_por_ruta(ruta_activa)
    elementos = elementos_navegacion(pilar.identificador) if pilar is not None else ()
    with ui.element("div").classes("navegacion-centro"):
        _renderizar_elementos_centro(pilar, elementos, clave_activa)

    with ui.element("div").classes("tema-boton-selector navegacion-tema"):
        renderizar_accesos_algebra()
        renderizar_boton_tema()


def _renderizar_elementos_centro(pilar: Any, elementos: Any, clave_activa: str) -> None:
    """Renderiza el distintivo del pilar y los accesos a sus herramientas."""
    if pilar is None or len(elementos) == 0:
        return
    with ui.element("span").classes("navegacion-pilar"):
        ui.html(icono_svg(pilar.icono))
        ui.html(html.escape(pilar.nombre_corto), tag="span").classes("navegacion-nombre-pilar")

    with ui.element("nav").classes("navegacion-elementos").props(
        f'aria-label="Herramientas de {pilar.nombre_corto}"'
    ):
        for elemento in elementos:
            _renderizar_elemento_pilar(elemento, clave_activa)



def _renderizar_elemento_pilar(elemento: Any, clave_activa: str) -> None:
    """Renderiza un elemento de navegación individual dentro de un pilar."""
    esta_activa = (elemento.clave == clave_activa)
    clases_elemento = "navegacion-accion navegacion-elemento" + (" navegacion-activa" if esta_activa else "")
    propiedades_elemento = f'href="{enlace_elemento_navegacion(elemento)}" aria-label="{elemento.etiqueta}" title="{elemento.etiqueta}"'
    if esta_activa:
        propiedades_elemento += ' aria-current="page"'
    with ui.element("a").classes(clases_elemento).props(propiedades_elemento).tooltip(elemento.etiqueta):
        ui.html(icono_svg(elemento.icono))
        ui.html(html.escape(elemento.etiqueta), tag="span").classes("navegacion-etiqueta-completa")
        ui.html(html.escape(elemento.etiqueta_corta), tag="span").classes("navegacion-etiqueta-breve")


def _registrar_navegacion_reciente(ruta_activa: str) -> None:
    """Registra la herramienta activa en el historial reciente del cliente y centra el foco."""
    from nicegui import context
    try:
        if not getattr(context.client, "has_socket_connection", False):
            return
        herramienta_activa = herramienta_por_ruta(ruta_activa)
        if herramienta_activa is not None:
            ui.run_javascript(
                f"window.scalaris?.recientes?.registrar?.({json.dumps(herramienta_activa.identificador)});"
            )
        ui.run_javascript("window.scalaris?.navegacion?.centrarActivo?.();")
    except Exception:
        pass
