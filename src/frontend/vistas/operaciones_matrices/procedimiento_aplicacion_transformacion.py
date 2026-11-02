"""Procedimiento de Av con foco de componente y ciclo de vida independiente del análisis."""
import json
from functools import partial

from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.versionado_recursos import versionar_html
from .pasos_aplicacion_transformacion import adaptar_pasos_aplicacion
from .reproductor_aplicacion_transformacion import ReproductorAplicacion

URL_COMPONENTES = versionar_html('src="/assets/js/aplicacion_transformacion.js"').split('"')[1]


def montar_procedimiento_aplicacion(resultado: dict, captura: dict, region, panel_ia=None) -> ReproductorPasos:
    """Monta navegación y explicación del paso sin alterar la escena al exportar."""
    pasos, grupos, componentes = adaptar_pasos_aplicacion(resultado, captura)
    identificador = region.props.get("id", region.html_id)
    tiene_grafica = any(isinstance(elemento, ui.plotly) for elemento in region.descendants())
    ui.label(textos.COMPROBACION_APLICACION).classes("texto-secundario text-sm")
    aviso = ui.label(textos.COMPONENTE_SIN_SELECCION).classes("texto-principal text-sm w-full").props(
        'role="status" aria-live="polite" data-componente-actual')

    def renderizar(paso, contenedor):
        """Muestra una fórmula y señala su componente sin reconstruir las escenas."""
        with contenedor:
            paso.cuerpo()
        if contenedor is not reproductor.contenedor_cuerpo:
            return
        componente = componentes[paso.indice]
        aviso.set_text(_describir_componente(resultado, componente, tiene_grafica))
        indice = -1 if componente is None else componente
        ui.run_javascript(
            f'import({json.dumps(URL_COMPONENTES)}).then(() => '
            f'window.scalaris.aplicacionTransformacion.actualizar({json.dumps(identificador)}, {indice}));')

    reproductor = ReproductorAplicacion(pasos, grupos, renderizar, f"aplicacion-{region.id}", opciones={
        "titulo": textos.PROCEDIMIENTO_APLICACION,
        "al_explicar": (partial(_explicar_vigente, region, crear_accion_explicacion(panel_ia, pasos))
                        if panel_ia else None),
        "esta_ocupado": lambda: bool(getattr(panel_ia, "_esta_enviando", False)),
    })
    reproductor.construir()
    return reproductor


def _explicar_vigente(region, accion, paso) -> None:
    if not region.is_deleted:
        accion(paso)


def _describir_componente(resultado: dict, componente: int | None, tiene_grafica: bool) -> str:
    if componente is None:
        return textos.COMPONENTE_SIN_SELECCION
    exacta = resultado["vector_transformado"]["exacta"][componente]
    mensaje = textos.COMPONENTE_ACTIVA if tiene_grafica else textos.COMPONENTE_SIN_GRAFICA
    return mensaje.format(indice=componente + 1, valor=exacta)


def detener_procedimiento_aplicacion(vista) -> None:
    """Retira el reproductor de aplicación antes de invalidar su captura o cliente."""
    reproductor = getattr(vista, "reproductor_aplicacion", None)
    if reproductor is not None:
        reproductor.detener()
    vista.reproductor_aplicacion = None
