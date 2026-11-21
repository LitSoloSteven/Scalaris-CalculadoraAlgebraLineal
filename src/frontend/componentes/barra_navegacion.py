"""Barra de navegación contextual y de acceso rápido para Scalaris."""
from __future__ import annotations

import html
import json
from typing import Any
from nicegui import ui


from src.frontend.nucleo import banderas
from src.frontend.componentes.aplicacion.base.iconos import icono_svg
from src.frontend.componentes.selector_tema import renderizar_boton_tema
from src.frontend.navegacion import (
    RUTA_INICIO,
    ORDEN_NAVEGACION_PLANA,
    predeterminado_elemento_clave,
    enlace_elemento_navegacion,
    elementos_navegacion,
    herramienta_por_identificador,
    herramienta_por_ruta,
)
from src.frontend.navegacion.modelo import ElementoNavegacion
from src.frontend.navegacion.secciones_inicio import SeccionInicio, seccion_por_clave

_CLAVES_ESCENAS = frozenset(elemento.clave for elemento in elementos_navegacion("visualizador"))
_ETIQUETAS_CONTEXTUALES = {"vis:vectores": "Vectores del Visualizador"}


def crear_barra_navegacion(interfaz_activa=None, ruta_activa: str = "/", clave_activa: str | None = None, al_alternar_ia=None):
    """Genera la barra plana o contextual por secciones según banderas."""
    clave_activa = predeterminado_elemento_clave(ruta_activa) if clave_activa is None else clave_activa
    contextual = banderas.navegacion_actualizada()

    with ui.header().classes("navegacion-cabecera").props("reveal"):
        _renderizar_logotipo()
        with ui.element("div").classes("panel-tarjeta navegacion-capsula pointer-events-auto"):
            if not contextual:
                _renderizar_barra_plana(interfaz_activa, ruta_activa, al_alternar_ia)
            else:
                _renderizar_barra_contextual(clave_activa)

    _registrar_navegacion_reciente(ruta_activa, clave_activa=clave_activa, centrar=contextual)


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


def _renderizar_barra_contextual(clave_activa: str | None) -> None:
    """Renderiza la botonera contextual con la sección del acceso activo."""
    with ui.element("a").classes("navegacion-accion navegacion-inicio").props(
        f'href="{RUTA_INICIO}" aria-label="Inicio" title="Inicio"'
    ).tooltip("Inicio"):
        ui.html(icono_svg("inicio"))

    seccion = seccion_por_clave(clave_activa)
    with ui.element("div").classes("navegacion-centro"):
        if seccion is not None:
            _renderizar_seccion(seccion, clave_activa)

    with ui.element("div").classes("tema-boton-selector navegacion-tema"):
        renderizar_boton_tema()


def _renderizar_seccion(seccion: SeccionInicio, clave_activa: str | None) -> None:
    """Renderiza el símbolo, el título y los accesos de una sección del directorio."""
    with ui.element("span").classes("navegacion-seccion"):
        ui.html(icono_svg(seccion.icono), tag="span")
        ui.html(html.escape(seccion.titulo), tag="span")

    with ui.element("div").classes("navegacion-recorrido"):
        ui.html("‹", tag="span").classes("navegacion-indicio navegacion-indicio-antes").props('aria-hidden="true"')
        with ui.element("nav").classes("navegacion-elementos").props(
            f'aria-label="Herramientas de {seccion.titulo}"'
        ):
            for elemento in seccion.accesos:
                _renderizar_acceso(elemento, clave_activa)
        ui.html("›", tag="span").classes("navegacion-indicio navegacion-indicio-despues").props('aria-hidden="true"')


def _renderizar_acceso(elemento: ElementoNavegacion, clave_activa: str | None) -> None:
    """Renderiza un acceso y distingue la escena de Vectores de la herramienta."""
    esta_activa = (elemento.clave == clave_activa)
    etiqueta = _ETIQUETAS_CONTEXTUALES.get(elemento.clave, elemento.etiqueta)
    clases_elemento = "navegacion-accion navegacion-elemento" + (" navegacion-activa" if esta_activa else "")
    propiedades_elemento = f'href="{enlace_elemento_navegacion(elemento)}" aria-label="{etiqueta}" title="{etiqueta}"'
    if esta_activa:
        propiedades_elemento += ' aria-current="page"'
    with ui.element("a").classes(clases_elemento).props(propiedades_elemento).tooltip(etiqueta):
        ui.html(icono_svg(elemento.icono))
        ui.html(html.escape(etiqueta), tag="span").classes("navegacion-etiqueta-completa")


def _clave_reciente_valida(ruta_activa: str, clave_activa: str | None) -> str | None:
    """Devuelve el identificador o la clave de escena validada para el historial."""
    herramienta_activa = herramienta_por_ruta(ruta_activa)
    if herramienta_activa is None or not herramienta_activa.habilitada:
        return None
    if herramienta_activa.identificador == "visualizador":
        if clave_activa in _CLAVES_ESCENAS:
            return clave_activa
        return predeterminado_elemento_clave(ruta_activa)
    return herramienta_activa.identificador


def _registrar_navegacion_reciente(
    ruta_activa: str, clave_activa: str | None = None, centrar: bool = True
) -> None:
    """Registra la herramienta reciente y deja visible su enlace sin mover el foco."""
    from nicegui import context
    cliente = context.client
    clave_reciente = _clave_reciente_valida(ruta_activa, clave_activa)
    if clave_reciente is None and not centrar:
        return

    def registrar():
        """Espera la conexión inicial antes de enviar el registro al navegador."""
        if clave_reciente is not None:
            cliente.run_javascript(
                f"window.scalaris?.recientes?.registrar?.({json.dumps(clave_reciente)});"
            )
        if centrar:
            cliente.run_javascript("window.scalaris?.navegacion?.centrarActivo?.();")

    if cliente.has_socket_connection:
        registrar()
    else:
        cliente.on_connect(registrar)
