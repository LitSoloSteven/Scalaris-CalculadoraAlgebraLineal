"""Presentación del veredicto, base, familia, criterios y gráfica de subespacios."""
from __future__ import annotations

from functools import partial

from nicegui import ui

from src.frontend.componentes.reproductor_pasos.formato.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.interfaz.reproductor import ReproductorPasos
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    MODO_RESTRICCIONES,
    NOTA_GENERA_AMBIENTE,
    SUBTITULO_CONJUNTO_VACIO,
    SUBTITULO_SUBESPACIO_CERO,
    SUBTITULO_TEOREMA_CRITERIOS,
    SUBTITULO_TEOREMA_RESTRICCIONES_AFIN,
    SUBTITULO_TEOREMA_RESTRICCIONES_HOMOGENEO,
    SUBTITULO_TEOREMA_RESTRICCIONES_VACIO,
    TITULO_TEOREMA_CRITERIOS,
    TITULO_VERIFICACION_MOTOR,
    VEREDICTO_CONJUNTO_VACIO,
    VEREDICTO_SUBESPACIO_CERO,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.pasos_restricciones import (
    renderizar_verificacion_motor_item,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.pasos_subespacios import (
    crear_reproductor_subespacios,
)
from src.frontend.vistas.geometria.figuras.figura_subespacios import preparar_figura_subespacio

_CLASES_ESTADO = {
    "exito": "distintivo-exito subespacios-criterio-estado",
    "error": "distintivo-error subespacios-criterio-estado subespacios-criterio-error",
    "vacuo": "distintivo-advertencia subespacios-criterio-estado subespacios-criterio-vacuo",
}


def mostrar_resultado_subespacio(
    resultado: dict, *, tema: str = "papel"
) -> ReproductorPasos | None:
    """Renderiza el resultado exacto de subespacios y devuelve el reproductor si aplica."""
    if resultado.get("estado") != "EXITO":
        ui.label("No se pudo analizar el conjunto").classes(
            "text-lg font-semibold texto-principal"
        ).props("role=status")
        ui.label(str(resultado.get("mensaje") or "")).classes(
            "subespacios-numero texto-secundario"
        ).props("role=alert")
        return None
    reproductor, indices_criterios = crear_reproductor_subespacios(resultado)
    _mostrar_veredicto(resultado)
    if resultado.get("modo") == MODO_RESTRICCIONES:
        _mostrar_detalle_restricciones(resultado)
    else:
        _mostrar_base_y_dependencias(resultado)
    _mostrar_criterios(resultado, reproductor, indices_criterios)
    _mostrar_verificaciones_motor(resultado)
    _mostrar_figura(resultado, tema)
    reproductor.construir()
    return reproductor


def _metricas_resultado(resultado: dict) -> list[tuple[str, object]]:
    ambiente = f"ℝ^{resultado['dimension_ambiente']}"
    if resultado.get("modo") != MODO_RESTRICCIONES:
        return [
            ("Rango", resultado["rango"]),
            ("Dimensión", resultado["dimension"]),
            ("Ambiente", ambiente),
            ("Generadores", len(resultado.get("etiquetas_generadores") or ())),
        ]
    ecuaciones = resultado.get("cantidad_ecuaciones") or 0
    clasificacion = resultado.get("clasificacion")
    if clasificacion == "SUBESPACIO":
        return [("Rango", resultado["rango"]), ("Dimensión", resultado["dimension"]), ("Ambiente", ambiente), ("Ecuaciones", ecuaciones)]
    if clasificacion == "AFIN_NO_SUBESPACIO":
        return [("Rango", resultado["rango"]), ("Dimensión afín", resultado["dimension_afin"]), ("Ambiente", ambiente), ("Ecuaciones", ecuaciones)]
    metricas: list[tuple[str, object]] = [("Rango de A", resultado["rango"])]
    if resultado.get("rango_aumentada") is not None:
        metricas.append(("Rango de [A | b]", resultado["rango_aumentada"]))
    metricas.extend([("Ambiente", ambiente), ("Ecuaciones", ecuaciones)])
    return metricas


def _mostrar_veredicto(resultado: dict) -> None:
    ui.label(resultado["veredicto"]).classes(
        "text-lg font-semibold texto-principal"
    ).props("role=status")
    ui.label(resultado["subtitulo_veredicto"]).classes(
        "subespacios-numero texto-secundario text-sm"
    )
    with ui.row().classes("w-full flex-wrap gap-4"):
        for rotulo, valor in _metricas_resultado(resultado):
            with ui.column().classes("panel-tarjeta px-3 py-2 gap-0"):
                ui.label(rotulo).classes("text-xs texto-secundario")
                ui.label(str(valor)).classes("subespacios-numero font-bold texto-principal")
    if resultado.get("herencia_axiomas"):
        ui.label(resultado["herencia_axiomas"]).classes("text-sm texto-secundario")


def _mostrar_tarjeta_subespacio_cero() -> None:
    with ui.column().classes("w-full panel-tarjeta p-3 gap-1"):
        ui.label(VEREDICTO_SUBESPACIO_CERO).classes("font-semibold texto-principal")
        ui.label(SUBTITULO_SUBESPACIO_CERO).classes("subespacios-numero texto-secundario text-sm")


def _mostrar_base_y_dependencias(resultado: dict) -> None:
    if resultado.get("es_subespacio_cero"):
        _mostrar_tarjeta_subespacio_cero()
        return
    ui.label("Base extraída de los generadores originales").classes(
        "text-base font-semibold texto-principal mt-2"
    )
    etiquetas_base = resultado.get("etiquetas_generadores_base") or ()
    with ui.column().classes("w-full gap-2"):
        for etiqueta, vector in zip(etiquetas_base, resultado.get("base") or ()):
            _mostrar_vector_base(etiqueta, vector)
    _mostrar_dependencias(resultado.get("dependencias") or ())


def _mostrar_detalle_restricciones(resultado: dict) -> None:
    clasificacion = resultado.get("clasificacion")
    if clasificacion == "VACIO_NO_SUBESPACIO":
        _mostrar_bloque_vacio(resultado)
        return
    pivotes = ", ".join(resultado.get("variables_pivote") or ()) or "ninguna"
    libres = ", ".join(resultado.get("variables_libres") or ()) or "ninguna"
    ui.label(f"Variables pivote: {pivotes} · Variables libres: {libres}").classes(
        "subespacios-numero texto-secundario text-sm mt-1"
    )
    if clasificacion == "SUBESPACIO":
        _mostrar_bloque_homogeneo(resultado)
    else:
        _mostrar_bloque_afin(resultado)


def _mostrar_bloque_vacio(resultado: dict) -> None:
    with ui.column().classes("w-full panel-tarjeta p-3 gap-1 mt-1"):
        ui.label(VEREDICTO_CONJUNTO_VACIO).classes("font-semibold texto-principal")
        ui.label(SUBTITULO_CONJUNTO_VACIO).classes("subespacios-numero texto-secundario text-sm")
        testigo = resultado.get("testigo") or {}
        if testigo.get("descripcion"):
            ui.label(f"Testigo: {testigo['descripcion']}").classes(
                "subespacios-numero texto-principal text-sm select-text"
            )


def _mostrar_bloque_homogeneo(resultado: dict) -> None:
    if resultado.get("es_subespacio_cero"):
        _mostrar_tarjeta_subespacio_cero()
        return
    ui.label("Base del núcleo").classes("text-base font-semibold texto-principal mt-2")
    with ui.column().classes("w-full gap-2"):
        for indice, vector in enumerate(resultado.get("base") or (), 1):
            _mostrar_vector_base(f"d_{indice}", vector)
    _mostrar_familia_parametrica(resultado.get("familia_parametrica"), "Familia paramétrica del núcleo")


def _mostrar_bloque_afin(resultado: dict) -> None:
    testigo = resultado.get("testigo") or {}
    if testigo.get("descripcion"):
        with ui.column().classes("w-full panel-tarjeta p-3 gap-1 mt-1"):
            ui.label("Testigo del origen").classes("font-semibold texto-principal text-sm")
            ui.label(testigo["descripcion"]).classes("subespacios-numero texto-secundario text-sm select-text")
    particular = resultado.get("particular") or ()
    ui.label("Punto particular y direcciones de ker(A)").classes(
        "text-base font-semibold texto-principal mt-2"
    )
    _mostrar_vector_base("p", particular)
    direcciones = resultado.get("direcciones") or ()
    if not direcciones:
        ui.label("El núcleo es {0}; la solución es un punto afín único.").classes("texto-secundario text-sm")
    else:
        with ui.column().classes("w-full gap-2"):
            for indice, vector in enumerate(direcciones, 1):
                _mostrar_vector_base(f"d_{indice}", vector)
    _mostrar_familia_parametrica(resultado.get("familia_parametrica"), "Familia afín p + ker(A)")


def _mostrar_familia_parametrica(familia: dict | None, titulo: str) -> None:
    if not familia:
        return
    ui.label(titulo).classes("text-sm font-semibold texto-principal mt-2")
    with ui.column().classes("subespacios-formula gap-1"):
        if familia.get("latex"):
            renderizar_latex(familia["latex"], vigilar_region=True)
        ui.label(familia["texto"]).classes("subespacios-numero texto-secundario text-sm select-text")


def _mostrar_vector_base(etiqueta: str, vector: tuple[str, ...]) -> None:
    with ui.row().classes("w-full items-center gap-2 no-wrap"):
        etiqueta_ui = ui.label(etiqueta).classes("subespacios-etiqueta font-semibold texto-principal")
        etiqueta_ui.props.update({"title": etiqueta})
        ui.label(f"= ({', '.join(vector)})").classes("subespacios-numero texto-principal select-text min-w-0")


def _mostrar_dependencias(dependencias: tuple[dict, ...]) -> None:
    if not dependencias:
        return
    ui.label("Generadores redundantes (no invalidan la familia):").classes(
        "text-sm font-semibold texto-secundario mt-1"
    )
    for dependencia in dependencias:
        if dependencia.get("respaldada") and dependencia.get("latex"):
            renderizar_latex(dependencia["latex"], vigilar_region=True)
        ui.label(dependencia["texto"]).classes("subespacios-numero texto-secundario text-sm select-text")


def _subtitulo_criterios(resultado: dict) -> str:
    if resultado.get("modo") != MODO_RESTRICCIONES:
        return SUBTITULO_TEOREMA_CRITERIOS
    clasificacion = resultado.get("clasificacion")
    if clasificacion == "SUBESPACIO":
        return SUBTITULO_TEOREMA_RESTRICCIONES_HOMOGENEO
    if clasificacion == "AFIN_NO_SUBESPACIO":
        return SUBTITULO_TEOREMA_RESTRICCIONES_AFIN
    return SUBTITULO_TEOREMA_RESTRICCIONES_VACIO


def _mostrar_criterios(
    resultado: dict, reproductor: ReproductorPasos, indices_criterios: dict[str, int]
) -> None:
    ui.label(TITULO_TEOREMA_CRITERIOS).classes("text-base font-semibold texto-principal mt-3")
    ui.label(_subtitulo_criterios(resultado)).classes("text-xs texto-secundario")
    with ui.column().classes("subespacios-criterios w-full gap-2"):
        for criterio in resultado.get("criterios") or ():
            indice = indices_criterios.get(criterio["clave"], 0)
            clase_estado = _CLASES_ESTADO.get(criterio.get("clase_estado", "exito"), _CLASES_ESTADO["exito"])
            boton = ui.button(
                on_click=partial(reproductor._seleccionar_desde_indice, indice),
                color=None,
            ).classes("boton-discreto subespacios-criterio-boton w-full justify-between px-3 py-2")
            boton.props("ripple=false")
            boton.props.update({
                "aria-label": f"{criterio['titulo']}: {criterio['estado']}. Ir a la demostración",
                "aria-controls": reproductor.id_tarjeta,
            })
            with boton, ui.row().classes("w-full items-center justify-between gap-2 no-wrap"):
                ui.label(criterio["titulo"]).classes("texto-principal text-sm font-medium text-left min-w-0")
                ui.label(criterio["estado"]).classes(f"{clase_estado} px-2 py-1 text-xs font-bold shrink-0")


def _mostrar_verificaciones_motor(resultado: dict) -> None:
    comprobaciones = resultado.get("comprobaciones") or ()
    if not comprobaciones:
        return
    ui.label(TITULO_VERIFICACION_MOTOR).classes("text-sm font-semibold texto-secundario mt-2")
    with ui.column().classes("w-full gap-1"):
        for elemento in comprobaciones:
            renderizar_verificacion_motor_item(elemento)


def _mostrar_figura(resultado: dict, tema: str) -> None:
    figura_preparada = preparar_figura_subespacio(resultado, tema=tema)
    ui.label("Representación geométrica").classes("text-base font-semibold texto-principal mt-3")
    ui.label(figura_preparada.descripcion).classes("texto-secundario text-sm")
    if not figura_preparada.disponible:
        ui.label(figura_preparada.motivo_indisponible or "").classes("texto-secundario text-sm")
        return
    if resultado.get("es_subespacio") and resultado.get("dimension_ambiente") == 3 and resultado.get("dimension") == 3:
        ui.label(NOTA_GENERA_AMBIENTE).classes("texto-principal text-sm font-semibold")
    clase = "subespacios-figura subespacios-figura-1d w-full" if figura_preparada.es_1d else "subespacios-figura w-full"
    with ui.element("div").classes(clase) as marco:
        marco.props.update({"role": "img", "aria-label": figura_preparada.descripcion})
        grafica = ui.plotly(figura_preparada.figura).classes("w-full h-full")
        grafica.on("plotly_afterplot", js_handler="() => window.scalaris?.sincronizarTemaPlotly?.()")
