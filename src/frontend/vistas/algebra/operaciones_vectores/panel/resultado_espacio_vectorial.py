"""Veredicto y procedimiento de axiomas para las operaciones personalizadas."""
from functools import partial

from nicegui import ui

from src.frontend.componentes.exportacion_pdf.montaje.integracion import region_pdf
from src.frontend.componentes.glosa.interaccion.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.reproductor_pasos.interfaz.reproductor import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.nucleo.modelo import GrupoReproductor, PasoReproductor
from src.frontend.controladores.algebra.operaciones_vectores.presentacion_espacio_vectorial import (
    evidencia_axioma, formatear_vector,
)
from src.frontend.nucleo.textos.textos_espacio_vectorial import ESTADOS_AXIOMA, NOMBRES_AXIOMAS, NOMBRES_OPERACIONES

_CLASES_ESTADO = {
    "CUMPLE": "distintivo-exito",
    "NO_CUMPLE": "distintivo-error",
    "NO_VERIFICADO": "distintivo-advertencia",
}


def mostrar_resultado_espacio(resultado: dict, *, panel_ia=None, sigue_vigente=None) -> ReproductorPasos | None:
    """Muestra veredicto y operaciones y conecta cada axioma con su evidencia exacta."""
    with region_pdf("espacios_subespacios-resumen"):
        _mostrar_resumen(resultado)
    comprobaciones = resultado["comprobaciones"]
    if not comprobaciones:
        return None
    reproductor = _crear_reproductor(comprobaciones, panel_ia, sigue_vigente)
    with region_pdf("espacios_subespacios-axiomas"):
        ui.label("Axiomas").classes("text-base font-semibold texto-principal")
        for paso, comprobacion in zip(reproductor.pasos, comprobaciones):
            _mostrar_enlace_axioma(reproductor, paso, comprobacion["estado"])
    if panel_ia is not None:
        panel_ia.renderizar_sugerencias_en_linea()
    reproductor.construir()
    return reproductor


def _mostrar_resumen(resultado: dict) -> None:
    ui.label(resultado["veredicto"]).classes("text-lg font-semibold texto-principal").props("role=status")
    diagnostico = resultado["diagnostico"]
    if diagnostico:
        ui.label(diagnostico["mensaje"]).classes("subespacios-numero texto-secundario")
    dimension = resultado["dimension_ambiente"]
    if dimension is not None:
        ui.label(f"Escalares en ℝ · vectores en ℝ^{dimension}").classes("texto-secundario")
    neutro = resultado["vector_cero"]
    if neutro is not None:
        ui.label(f"Neutro aditivo = {formatear_vector(neutro)}").classes("subespacios-numero texto-principal")
    for campo, coordenadas in resultado["operaciones"].items():
        ui.label(NOMBRES_OPERACIONES[campo]).classes("font-semibold texto-principal")
        for indice, coordenada in enumerate(coordenadas, 1):
            ui.label(f"Coordenada {indice} = {coordenada}").classes("subespacios-numero texto-secundario")


def _crear_reproductor(comprobaciones: tuple, panel_ia, sigue_vigente) -> ReproductorPasos:
    pasos = tuple(_crear_paso(indice, comprobacion) for indice, comprobacion in enumerate(comprobaciones))
    grupo = GrupoReproductor(
        "Axiomas del espacio vectorial", "Identidades polinómicas sobre ℝ", "verificacion", tuple(range(len(pasos))),
    )
    opciones = {
        "sin_movimiento": True, "tipos_leyenda": ("verificacion",),
        "al_explicar": crear_accion_explicacion(panel_ia, pasos, sigue_vigente=sigue_vigente),
        "esta_ocupado": lambda: bool(getattr(panel_ia, "_esta_enviando", False)),
    }
    return ReproductorPasos(pasos, (grupo,), _renderizar_evidencia, "espacio-vectorial", opciones)


def _crear_paso(indice: int, comprobacion: dict) -> PasoReproductor:
    titulo = NOMBRES_AXIOMAS[comprobacion["axioma"]]
    estado = ESTADOS_AXIOMA[comprobacion["estado"]]
    explicacion = comprobacion["explicacion"]
    return PasoReproductor(
        indice=indice, tipo="verificacion", descripcion=titulo, explicacion=explicacion,
        etiqueta_tipo=estado, cuerpo=comprobacion,
        meta_explicar={
            "operacion": titulo, "tipo": "verificacion", "origen": "axioma", "detalle": f"{estado}. {explicacion}",
        },
    )


def _mostrar_enlace_axioma(reproductor: ReproductorPasos, paso: PasoReproductor, estado: str) -> None:
    boton = ui.button(on_click=partial(reproductor.ir_a, paso.indice), color=None)
    boton.classes("boton-discreto subespacios-criterio-boton w-full")
    nombre = f"Ver desarrollo · {paso.descripcion} · {ESTADOS_AXIOMA[estado]}"
    boton.props(f'ripple=false aria-label="{nombre}"')
    with boton, ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
        ui.label(paso.descripcion).classes("text-left")
        ui.label(ESTADOS_AXIOMA[estado]).classes(_CLASES_ESTADO[estado])


def _renderizar_evidencia(paso: PasoReproductor, contenedor) -> None:
    with contenedor:
        for linea in evidencia_axioma(paso.cuerpo):
            ui.label(linea).classes("subespacios-numero texto-secundario")
